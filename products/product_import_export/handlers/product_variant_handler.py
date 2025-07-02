# your_app/graphql/handlers/product_variant_handler.py
from .base_handler import BaseHandler
from .attribute_handler import AttributeHandler # To handle variant attributes
from ...models import ProductVariant, Product, Attribute, VariantAttribute, ProductImage # Adjusted paths
from ..helpers import handle_image_import # For variant image (if any)
from django.utils.text import slugify

class ProductVariantHandler(BaseHandler):
    model = ProductVariant
    required_fields = ['name'] # Name of the variant itself
    # Lookup for a variant is typically its name *within* a specific product.
    # So, the ProductHandler will pass the product_instance.
    lookup_field = 'name' 

    def handle(self, data, product_instance=None):
        """
        Handles the creation or update of a ProductVariant.
        - data: Dict containing variant data (e.g., 'name', 'sku', 'attributes', 'image_id' etc.).
        - product_instance: The Product instance this variant belongs to. Required.
        """
        errors = []
        if not product_instance:
            errors.append("Product instance is required to handle a product variant.")
            return {'instance': None, 'status': 'error', 'errors': errors}

        if not self.validate_data(data, errors): # Validates 'name' field in data
            return {'instance': None, 'status': 'error', 'errors': errors}

        variant_name = data.get(self.lookup_field)
        
        # Lookup for variant is based on product_instance and variant_name
        variant_lookup_params = {
            'product': product_instance,
            self.lookup_field: variant_name, # e.g., 'name': 'Red'
        }

        # Prepare defaults for creation or update
        variant_defaults = {
            'sku': data.get('sku'), # Model's save method handles auto-generation if blank and not provided
            'barcode': data.get('barcode'),
            'additional_price': data.get('additional_price', 0.00),
            'stock': data.get('stock', 0),
            'is_active': data.get('is_active', True),
        }
        # Remove None values from defaults unless they are meant to clear a field
        variant_defaults = {k: v for k, v in variant_defaults.items() if v is not None}


        # Handle variant-specific image if an 'image_id' (FK to ProductImage) is provided
        # This assumes the ProductImage itself is already created and associated with the parent product.
        image_id_for_variant = data.get('image_id') 
        if image_id_for_variant:
            try:
                # Ensure the image belongs to the same product to prevent linking to unrelated product images
                product_image_instance = ProductImage.objects.get(id=image_id_for_variant, product=product_instance)
                variant_defaults['image'] = product_image_instance
            except ProductImage.DoesNotExist:
                errors.append(f"ProductImage with id '{image_id_for_variant}' not found for product '{product_instance.name}' to link to variant '{variant_name}'.")
            except ValueError: # Handles if image_id_for_variant is not a valid UUID/int
                 errors.append(f"Invalid image_id format '{image_id_for_variant}' for variant '{variant_name}'.")


        instance = None
        status = 'skipped' # Default status

        try:
            if self.update_existing:
                instance, created = self.model.objects.update_or_create(
                    defaults=variant_defaults,
                    **variant_lookup_params # e.g. product=product_instance, name=variant_name
                )
                status = 'created' if created else 'updated'
            else: # Not updating existing variant's own fields
                try:
                    instance = self.model.objects.get(**variant_lookup_params)
                    status = 'skipped' # Found, but not updating variant's own fields. Attributes might still be processed.
                except self.model.DoesNotExist:
                    if self.create_related: # Can we create this new variant?
                        create_data = {**variant_defaults, **variant_lookup_params}
                        instance = self.model.objects.create(**create_data)
                        status = 'created'
                    else:
                        errors.append(f"Variant '{variant_name}' for product '{product_instance.name}' not found, and creation is disallowed.")
                        status = 'error'
                except self.model.MultipleObjectsReturned: # Should not happen if (product, name) is unique for variants
                    errors.append(f"Multiple variants named '{variant_name}' found for product '{product_instance.name}'. This indicates a data integrity issue.")
                    status = 'error'
        
        except Exception as e:
            errors.append(f"Error processing variant core '{variant_name}' for product '{product_instance.name}': {str(e)}")
            status = 'error'
        
        if not instance or status == 'error': # If variant creation/retrieval failed, stop.
            return {'instance': instance, 'status': status if status == 'error' else 'error', 'errors': errors}

        # --- Handle Variant Attributes (through VariantAttribute model) ---
        # Expected format for attributes in data: {'AttributeName1': 'Value1', 'AttributeName2': 'Value2'}
        variant_attributes_input = data.get('attributes', {}) 
        
        # Only process attributes if the variant was successfully created/updated or if it existed and we are allowed to update related
        if variant_attributes_input is not None and (status in ['created', 'updated'] or (status == 'skipped' and self.update_existing)):
            attribute_handler = AttributeHandler(update_existing=self.update_existing, create_related=self.create_related)
            
            current_variant_attrs = {va.attribute.name: va for va in instance.variantattribute_set.all()}
            new_attr_values_to_set = []

            for attr_name, attr_value_from_input in variant_attributes_input.items():
                # Get or create the global Attribute object (e.g., "Color", "Size")
                attribute_object_result = attribute_handler.handle({'name': attr_name})
                
                if attribute_object_result['instance']:
                    attribute_master_instance = attribute_object_result['instance']
                    new_attr_values_to_set.append((attribute_master_instance, attr_value_from_input))
                    
                    # Remove from current_variant_attrs if it's in the input, so we know what to delete later
                    if attr_name in current_variant_attrs:
                        del current_variant_attrs[attr_name] 
                else:
                    for err_msg in attribute_object_result['errors']:
                        errors.append(f"Variant '{variant_name}' attribute '{attr_name}' resolution error: {err_msg}")

            # Delete VariantAttribute entries that were not in the new input (if updating)
            if self.update_existing or status == 'updated': # Check status as well
                for attr_name_to_delete, variant_attr_instance_to_delete in current_variant_attrs.items():
                    variant_attr_instance_to_delete.delete()
            
            # Create or Update VariantAttribute entries
            for attr_master, attr_val in new_attr_values_to_set:
                VariantAttribute.objects.update_or_create(
                    variant=instance,
                    attribute=attr_master,
                    defaults={'value': attr_val}
                )
        elif variant_attributes_input is None and (self.update_existing or status == 'updated'): # Explicitly clear if 'attributes' is null and updating
            instance.variantattribute_set.all().delete()


        final_status = status
        if errors and status not in ['error', 'skipped']: # If there were errors during attribute processing
            final_status = 'completed_with_errors'

        return {'instance': instance, 'status': final_status, 'errors': errors}
