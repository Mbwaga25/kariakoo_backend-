# your_app/graphql/handlers/product_image_handler.py
from .base_handler import BaseHandler
from ..helpers import handle_image_import # Ensure this helper can download URLs and convert to WebP
from ...models import ProductImage, Product # Adjusted path to app's models
from django.utils.text import slugify
from django.core.files.base import ContentFile # For type checking if needed

class ProductImageHandler(BaseHandler):
    model = ProductImage
    # 'image_source' will be the key in the input data for URL or base64 string
    required_fields = ['image_source'] 
    # No single lookup_field for images apart from product context; typically identified by 'order' or content.

    def handle(self, data, product_instance=None):
        """
        Handles the creation or update of a ProductImage.
        - data: Dict containing image data (e.g., 'image_source', 'alt_text', 'is_primary', 'order').
        - product_instance: The Product instance this image belongs to. Required.
        """
        errors = []
        if not product_instance:
            errors.append("Product instance is required to handle a product image.")
            return {'instance': None, 'status': 'error', 'errors': errors}

        # Use 'image_source' from input data, which can be a URL or base64
        # The required_fields check in BaseHandler should use 'image_source'
        # Forcing self.required_fields here if BaseHandler's init doesn't allow override easily
        current_required_fields = ['image_source']
        is_data_valid = True
        for field in current_required_fields:
            if not data.get(field):
                errors.append(f"Field '{field}' is required for ProductImage.")
                is_data_valid = False
        if not is_data_valid:
             return {'instance': None, 'status': 'error', 'errors': errors}


        image_src_input = data.get('image_source') # This is the URL or base64 from CSV/JSON
        
        # Set defaults for other fields
        alt_text = data.get('alt_text')
        if alt_text is None: # Explicitly set default if not provided at all
            alt_text = f"{product_instance.name} image" if product_instance.name else "Product image"
        
        is_primary_input = data.get('is_primary')
        is_primary = False # Default
        if isinstance(is_primary_input, str):
            is_primary = is_primary_input.strip().lower() == 'true'
        elif isinstance(is_primary_input, bool):
            is_primary = is_primary_input
            
        order_input = data.get('order')
        order = 0 # Default
        try:
            if order_input is not None:
                order = int(order_input)
        except ValueError:
            errors.append(f"Invalid order value '{order_input}'. Must be an integer.")
            # Continue with default order or handle error more strictly

        # Attempt to download/process the image using the helper
        image_file_name_prefix = f"product_{product_instance.slug or product_instance.id}_order_{order}"
        downloaded_image_file = None
        original_image_url_to_store = None

        if isinstance(image_src_input, str) and image_src_input.startswith('http'):
            original_image_url_to_store = image_src_input # Store the original URL
            # The handle_image_import helper should download from URL and convert to WebP
            downloaded_image_file = handle_image_import(image_src_input, image_file_name_prefix) 
            if not downloaded_image_file:
                errors.append(f"Failed to download or process image from URL: {image_src_input} for product '{product_instance.name}'. The URL will be stored directly.")
                # No critical error yet, we'll store the URL.
        elif isinstance(image_src_input, str) and image_src_input.startswith('data:image'):
            # It's a base64 string, handle_image_import should process it (e.g. to WebP)
            downloaded_image_file = handle_image_import(image_src_input, image_file_name_prefix)
            if not downloaded_image_file:
                 errors.append(f"Failed to process base64 image data for product '{product_instance.name}'.")
                 # This might be a more critical error if base64 processing fails.
        else:
            errors.append(f"Invalid image_source format: '{image_src_input}'. Must be a URL or base64 data URI.")
            # This is a critical error for the image itself.

        if not downloaded_image_file and not original_image_url_to_store:
            # If image_source was invalid and not a URL, we have nothing to store.
            return {'instance': None, 'status': 'error', 'errors': errors}


        image_orm_defaults = {
            'product': product_instance,
            'image': downloaded_image_file, # This will be the ContentFile (WebP) or None
            'image_url': original_image_url_to_store, # Store the original source URL
            'alt_text': alt_text,
            'is_primary': is_primary,
            'order': order,
        }

        instance = None
        status = 'skipped'

        # If there were errors during pre-processing (like invalid order) but we can still proceed
        if errors and not (not downloaded_image_file and not original_image_url_to_store):
            status = 'completed_with_errors' # Mark that there were issues but we might still save

        try:
            # For images, update_existing attempts to find an image by 'order' for this product.
            # If found, it updates it. If not found, it creates a new one if create_related is True.
            if self.update_existing:
                instance, created = self.model.objects.update_or_create(
                    product=product_instance,
                    order=order, # Lookup by product and order
                    defaults=image_orm_defaults
                )
                if created:
                    status = 'created'
                else: # Instance was updated
                    # If the image file changed, the old one is handled by Django's ImageField update process
                    # or by explicit delete if `instance.image.delete(save=False)` was used before setting new one.
                    # `update_or_create` with `defaults` handles this.
                    status = 'updated'
            else: # Not updating existing, only create if allowed and no conflict
                if self.create_related:
                    # Check if an image with this order already exists to avoid unintentional overwrites if not updating
                    if self.model.objects.filter(product=product_instance, order=order).exists():
                        errors.append(f"Image for product '{product_instance.name}' at order '{order}' already exists. 'Update existing' is false, so skipping.")
                        status = 'skipped' 
                    else:
                        instance = self.model.objects.create(**image_orm_defaults)
                        status = 'created'
                else: 
                    # If not creating and not updating, and it doesn't exist, it's effectively skipped.
                    # If it did exist, it would also be skipped as update_existing is false.
                    if not self.model.objects.filter(product=product_instance, order=order).exists():
                         errors.append(f"Creation of new image (order {order}) is disallowed for product '{product_instance.name}'.")
                    status = 'skipped'

        except Exception as e:
            # Catch Django ValidationErrors or other database issues
            if hasattr(e, 'message_dict'): 
                 for field, msgs in e.message_dict.items():
                     for msg in msgs: errors.append(f"Validation error on image field '{field}': {msg}")
            elif hasattr(e, 'messages') and isinstance(e.messages, list):
                 for msg in e.messages: errors.append(f"Validation error on image: {msg}")
            else:
                 errors.append(f"Error saving image for product '{product_instance.name}': {str(e)}")
            
            status = 'error' # Override status to error
            if instance: instance = None # Ensure instance is None if save failed
        
        # Refine final status based on errors accumulated
        if errors:
            if status not in ['error', 'skipped']: # If it was created/updated but had pre-processing errors
                final_status = 'completed_with_errors'
            else: # If it was already an error or skipped (potentially with new errors)
                final_status = status # Keep 'error' or 'skipped'
        else: # No errors at all
            final_status = status

        return {'instance': instance, 'status': final_status, 'errors': errors}

