# your_app/graphql/handlers/product_handler.py
from django.db import transaction # Recommended if ProductHandler itself does multiple saves
from .base_handler import BaseHandler
from ...models import Product, ProductAttributeValue, ProductImage, Tag, Attribute # Adjusted import paths
# Import other handlers
from .brand_handler import BrandHandler
from .category_handler import CategoryHandler
from .tag_handler import TagHandler
from .attribute_handler import AttributeHandler
from .product_image_handler import ProductImageHandler
from .product_variant_handler import ProductVariantHandler
from .product_segment_handler import ProductSegmentHandler
from decimal import Decimal, InvalidOperation # For price conversion
import json # For parsing JSON strings from CSV

class ProductHandler(BaseHandler):
    model = Product
    required_fields = ['name']
    lookup_field = 'name'

    def _handle_related_single(self, handler_class, related_data, field_name_for_error, current_errors):
        """Helper to process a single related entity (e.g., brand, category)."""
        if not related_data: # Handles empty string from CSV or None
            return None
        
        # Ensure related_data is a dict if a simple identifier (e.g., name string) was passed
        if not isinstance(related_data, dict):
            # Assuming the primary identifier for the related object is 'name' if not a dict
            related_data = {'name': related_data} 
            
        related_handler = handler_class(
            update_existing=self.update_existing,
            create_related=self.create_related
        )
        result = related_handler.handle(related_data)

        if result['errors']:
            for err in result['errors']:
                current_errors.append(f"{field_name_for_error} ('{related_data.get('name', 'N/A')}') error: {err}")
        
        return result['instance']

    def _handle_related_list(self, handler_class, list_data, field_name_for_error, current_errors, parent_instance=None):
        """
        Helper to process a list of related entities (e.g., tags, images, variants, segments).
        `parent_instance` is passed if the handler needs it (e.g., ProductImageHandler needs Product).
        """
        processed_instances = []
        if list_data is None: 
            return processed_instances 

        related_handler = handler_class(
            update_existing=self.update_existing,
            create_related=self.create_related
        )
        for item_data in list_data: # list_data is now expected to be a Python list of dicts or strings
            if not isinstance(item_data, dict): 
                item_data = {related_handler.lookup_field: item_data} 
            
            result = None
            if parent_instance and handler_class in [ProductImageHandler, ProductVariantHandler]: 
                result = related_handler.handle(item_data, product_instance=parent_instance)
            else: 
                result = related_handler.handle(item_data)
            
            if result and result['instance']:
                processed_instances.append(result['instance'])
            if result and result['errors']:
                 for err in result['errors']:
                    item_identifier = item_data.get('name', item_data.get('order', item_data.get('title', 'N/A')))
                    current_errors.append(f"{field_name_for_error} item ('{item_identifier}') error: {err}")
        return processed_instances


    def handle(self, data): # data here is a dict from a CSV row, all values are initially strings
        product_errors = [] 
        if not self.validate_data(data, product_errors): # Validates 'name' from CSV
            return {'instance': None, 'status': 'error', 'errors': product_errors}

        product_lookup_params, param_errors = self._get_lookup_params(data) # Uses 'name' from CSV
        if param_errors:
            product_errors.extend(param_errors)
            return {'instance': None, 'status': 'error', 'errors': product_errors}
        
        product_name = product_lookup_params.get(self.lookup_field)

        # --- Handle Related Entities First (Brand, Category) ---
        # CSV provides names for brand and category, e.g., data['brand_name'], data['category_name']
        brand_instance = self._handle_related_single(BrandHandler, data.get('brand_name'), "Brand", product_errors)
        category_instance = self._handle_related_single(CategoryHandler, data.get('category_name'), "Category", product_errors)

        if data.get('brand_name') and not brand_instance and not self.create_related:
            product_errors.append(f"Required Brand '{data.get('brand_name')}' not found and cannot be created.")
        if data.get('category_name') and not category_instance and not self.create_related:
            product_errors.append(f"Required Category '{data.get('category_name')}' not found and cannot be created.")
        
        if any("cannot be created" in err for err in product_errors if "Required" in err):
             return {'instance': None, 'status': 'error', 'errors': product_errors}

        # --- Type Conversions for specific fields from CSV string data ---
        price_str = data.get('price')
        processed_price = None
        if price_str is not None and price_str.strip() != '':
            try:
                processed_price = Decimal(price_str)
            except InvalidOperation:
                product_errors.append(f"Invalid price value: '{price_str}'. Must be a valid number.")
        
        rating_str = data.get('rating')
        processed_rating = None
        if rating_str is not None and rating_str.strip() != '':
            try:
                processed_rating = float(rating_str)
            except ValueError:
                product_errors.append(f"Invalid rating value: '{rating_str}'. Must be a valid number.")

        is_globally_active_str = data.get('is_globally_active')
        processed_is_globally_active = True # Default
        if isinstance(is_globally_active_str, str) and is_globally_active_str.strip() != '':
            processed_is_globally_active = is_globally_active_str.strip().lower() == 'true'
        # If is_globally_active_str is None or empty, it defaults to True as defined above.

        # --- Prepare Product Core Data ---
        product_defaults = {
            'description': data.get('description', ''), # Already a string from CSV
            'brand': brand_instance,
            'category': category_instance,
            'price': processed_price, 
            'rating': processed_rating,
            'is_globally_active': processed_is_globally_active,
            'meta_title': data.get('meta_title'),
            'meta_description': data.get('meta_description'),
            'meta_keywords': data.get('meta_keywords'),
        }
        final_product_defaults = {}
        for k, v in product_defaults.items():
            if k in ['brand', 'category']: 
                final_product_defaults[k] = v
            elif v is not None:
                final_product_defaults[k] = v
        product_defaults = final_product_defaults

        # --- Create or Update Product Instance ---
        product_instance = None
        product_status = 'skipped' 

        if product_errors: # If errors occurred during pre-processing (like type conversion)
            return {'instance': None, 'status': 'error', 'errors': product_errors}

        try:
            if self.update_existing:
                product_instance, created = self.model.objects.update_or_create(
                    defaults=product_defaults,
                    **product_lookup_params
                )
                product_status = 'created' if created else 'updated'
            else:
                try:
                    product_instance = self.model.objects.get(**product_lookup_params)
                    product_status = 'skipped' 
                except self.model.DoesNotExist:
                    if self.create_related: 
                        create_data = {**product_defaults, **product_lookup_params}
                        product_instance = self.model.objects.create(**create_data)
                        product_status = 'created'
                    else:
                        product_errors.append(f"Product '{product_name}' not found and creation is disallowed.")
                        product_status = 'error'
                except self.model.MultipleObjectsReturned:
                    product_errors.append(f"Multiple products found for '{product_name}'. Ensure lookup is unique.")
                    product_status = 'error'
        
        except Exception as e: 
            if hasattr(e, 'message_dict'): 
                 for field, messages in e.message_dict.items():
                     for message in messages:
                         product_errors.append(f"Validation error on field '{field}': {message}")
            elif hasattr(e, 'messages') and isinstance(e.messages, list): 
                 for message in e.messages:
                      product_errors.append(f"Validation error: {message}")
            else:
                 product_errors.append(f"Error processing product core '{product_name}': {str(e)}")
            product_status = 'error'

        if not product_instance or product_status == 'error':
            current_status = 'error' if not product_instance and product_status != 'error' else product_status
            return {'instance': None, 'status': current_status, 'errors': product_errors}

        # --- Handle Post-Save Relations (M2M, FKs on other models pointing to Product) ---
        # Tags: CSV provides a comma-separated string in 'tags' column
        tags_csv_string = data.get('tags', '') 
        if tags_csv_string is not None: 
            tags_list_from_csv = [tag.strip() for tag in tags_csv_string.split(',') if tag.strip()] if tags_csv_string else []
            processed_tags = self._handle_related_list(TagHandler, tags_list_from_csv, "Tag", product_errors)
            if product_status in ['created', 'updated'] or (product_status == 'skipped' and self.update_existing):
                product_instance.tags.set(processed_tags)

        # Product Attributes: CSV provides a JSON string in 'attributes_json' column
        attributes_json_string = data.get('attributes_json', '{}') 
        if attributes_json_string is not None:
            attributes_dict_from_json = {}
            try:
                attributes_dict_from_json = json.loads(attributes_json_string) if attributes_json_string else {}
                if not isinstance(attributes_dict_from_json, dict):
                    product_errors.append(f"Attributes JSON for '{product_name}' must be a valid JSON object (dictionary). Received: {attributes_json_string}")
                    attributes_dict_from_json = {}
            except json.JSONDecodeError:
                product_errors.append(f"Invalid JSON string for attributes for '{product_name}': {attributes_json_string}")
            
            if attributes_dict_from_json: # Only process if valid dict
                if product_status in ['created', 'updated'] or (product_status == 'skipped' and self.update_existing):
                    if self.update_existing or product_status == 'updated': 
                        product_instance.attribute_values.all().delete()
                    for attr_name, attr_value in attributes_dict_from_json.items():
                        attribute_master_instance = self._handle_related_single(
                            AttributeHandler, {'name': attr_name}, "Attribute", product_errors
                        )
                        if attribute_master_instance:
                            ProductAttributeValue.objects.update_or_create(
                                product=product_instance,
                                attribute=attribute_master_instance,
                                defaults={'value': str(attr_value)} 
                            )
        
        # Product Images: CSV provides a JSON string in 'images_json' column
        images_json_string = data.get('images_json', '[]') 
        if images_json_string is not None:
            images_list_from_json = []
            try:
                images_list_from_json = json.loads(images_json_string) if images_json_string else []
                if not isinstance(images_list_from_json, list):
                    product_errors.append(f"Images JSON for '{product_name}' must be a valid JSON array (list). Received: {images_json_string}")
                    images_list_from_json = []
            except json.JSONDecodeError:
                product_errors.append(f"Invalid JSON string for images for '{product_name}': {images_json_string}")

            if images_list_from_json: # Only process if valid list
                if product_status in ['created', 'updated'] or (product_status == 'skipped' and self.update_existing):
                    if self.update_existing or product_status == 'updated': 
                         product_instance.images.all().delete() 
                    self._handle_related_list(ProductImageHandler, images_list_from_json, "Image", product_errors, parent_instance=product_instance)

        # Product Variants: CSV provides a JSON string in 'variants_json' column
        variants_json_string = data.get('variants_json', '[]') 
        if variants_json_string is not None:
            variants_list_from_json = []
            try:
                variants_list_from_json = json.loads(variants_json_string) if variants_json_string else []
                if not isinstance(variants_list_from_json, list):
                    product_errors.append(f"Variants JSON for '{product_name}' must be a valid JSON array (list). Received: {variants_json_string}")
                    variants_list_from_json = []
            except json.JSONDecodeError:
                product_errors.append(f"Invalid JSON string for variants for '{product_name}': {variants_json_string}")
            
            if variants_list_from_json: # Only process if valid list
                if product_status in ['created', 'updated'] or (product_status == 'skipped' and self.update_existing):
                    if self.update_existing or product_status == 'updated': 
                        product_instance.variants.all().delete() 
                    self._handle_related_list(ProductVariantHandler, variants_list_from_json, "Variant", product_errors, parent_instance=product_instance)

        # Product Segments: CSV provides a comma-separated string in 'segments_list' column
        segments_csv_string = data.get('segments_list', '') 
        if segments_csv_string is not None:
            segments_list_from_csv = [seg.strip() for seg in segments_csv_string.split(',') if seg.strip()] if segments_csv_string else []
            processed_segments = self._handle_related_list(ProductSegmentHandler, segments_list_from_csv, "Segment", product_errors)
            if product_status in ['created', 'updated'] or (product_status == 'skipped' and self.update_existing):
                product_instance.segments.set(processed_segments)


        final_status = product_status
        if product_errors and product_status not in ['error', 'skipped']:
            final_status = 'completed_with_errors'
        elif product_status == 'skipped' and product_errors:
            final_status = 'skipped_with_errors' 

        return {
            'instance': product_instance,
            'status': final_status,
            'errors': product_errors
        }
