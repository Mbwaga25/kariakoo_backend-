# your_app/graphql/mutations.py
import graphene
from django.db import transaction
from .inputs import ImportInput # Your Graphene input types
from .helpers import process_csv_file, process_json_file # Your helper functions
from ..models import Product # Needed for fetching Product for image/variant handlers

# Import all handlers - adjust paths and structure as needed
# from .handlers.base_handler import BaseHandler # Not directly used in map, but good for context
from .handlers.brand_handler import BrandHandler
from .handlers.category_handler import CategoryHandler
from .handlers.attribute_handler import AttributeHandler
from .handlers.tag_handler import TagHandler
from .handlers.product_handler import ProductHandler
from .handlers.product_image_handler import ProductImageHandler
from .handlers.product_variant_handler import ProductVariantHandler
from .handlers.product_segment_handler import ProductSegmentHandler


class ImportDataMutation(graphene.Mutation):
    class Arguments:
        input = ImportInput(required=True)

    success = graphene.NonNull(graphene.Boolean)
    imported_count = graphene.Int(default_value=0)
    updated_count = graphene.Int(default_value=0)
    skipped_count = graphene.Int(default_value=0)
    error_count = graphene.Int(default_value=0)
    errors = graphene.List(graphene.NonNull(graphene.String)) # Detailed error messages

    @classmethod
    # @staff_member_required # Add your authentication/authorization if using graphql_jwt
    @transaction.atomic # Ensure the whole import is atomic
    def mutate(cls, root, info, input: ImportInput): # Use type hint for clarity
        
        handler_map = {
            # Ensure keys are lowercase as input.import_type is lowercased
            'brand': BrandHandler,
            'category': CategoryHandler,
            'attribute': AttributeHandler,
            'tag': TagHandler,
            'product': ProductHandler,
            'productimage': ProductImageHandler, # For direct import of product images
            'variant': ProductVariantHandler,     # For direct import of product variants
            'segment': ProductSegmentHandler,
        }

        import_type_lower = input.import_type.lower()
        HandlerClass = handler_map.get(import_type_lower)

        if not HandlerClass:
            return cls(success=False, errors=[f"Unsupported import type: {input.import_type}"], error_count=1)

        try:
            if input.file_type.lower() == 'csv':
                data_rows = process_csv_file(input.file_content)
            elif input.file_type.lower() == 'json':
                data_rows = process_json_file(input.file_content)
            else:
                return cls(success=False, errors=["Unsupported file type. Use CSV or JSON."], error_count=1)
        except Exception as e:
            return cls(success=False, errors=[f"Error parsing file: {str(e)}"], error_count=1)

        if not data_rows:
             return cls(success=True, errors=["No data found in file to import."], skipped_count=0) # No errors, but nothing to do.

        # Instantiate the handler with common flags
        handler_instance = HandlerClass(
            update_existing=input.update_existing,
            create_related=input.create_related
        )

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_messages = [] 

        for idx, row_data in enumerate(data_rows):
            # Attempt to get a meaningful identifier for error messages
            # This might need to be adapted based on the lookup_field of the specific handler
            row_identifier_key = getattr(handler_instance, 'lookup_field', 'name')
            if isinstance(row_identifier_key, list): # If lookup_field is a list
                row_identifier_key = row_identifier_key[0] # Take the first one for simple logging
            
            row_identifier = row_data.get(row_identifier_key, f"Row {idx+1}")


            try:
                result = None
                # Special handling for handlers that require a parent product_instance
                if HandlerClass in [ProductImageHandler, ProductVariantHandler]:
                    product_ref = row_data.get('product_name') or row_data.get('product_id') # Expect product identifier in row
                    if not product_ref:
                        error_messages.append(f"Missing 'product_name' or 'product_id' for {import_type_lower} '{row_identifier}'.")
                        continue # Skip this row

                    try:
                        # Determine if product_ref is ID or name (this is a simplification)
                        # A more robust system might require explicit 'product_lookup_field': 'id'/'name'
                        if isinstance(product_ref, int) or (isinstance(product_ref, str) and product_ref.isdigit()):
                             parent_product = Product.objects.get(id=product_ref)
                        else:
                             parent_product = Product.objects.get(name=product_ref) # Or slug, etc.
                    except Product.DoesNotExist:
                        error_messages.append(f"Parent Product '{product_ref}' not found for {import_type_lower} '{row_identifier}'.")
                        continue # Skip this row
                    except Product.MultipleObjectsReturned:
                        error_messages.append(f"Multiple Parent Products found for '{product_ref}' for {import_type_lower} '{row_identifier}'. Please use a unique identifier.")
                        continue

                    result = handler_instance.handle(row_data, product_instance=parent_product)
                else:
                    # Standard call for handlers like ProductHandler, BrandHandler, etc.
                    result = handler_instance.handle(row_data)
                
                status = result.get('status')
                row_errors = result.get('errors', [])

                # Consolidate counting based on status
                if status == 'created':
                    imported_count += 1
                elif status == 'updated':
                    updated_count += 1
                elif status == 'skipped':
                    skipped_count += 1
                elif status == 'completed_with_errors':
                    # Assume the main entity was processed (created or updated)
                    # This is an approximation; ideally, handler returns original action.
                    # For now, let's count it as an "update" that had side-errors.
                    updated_count += 1 
                elif status == 'skipped_with_errors':
                    skipped_count += 1
                # 'error' status does not increment main counts but errors are logged below.
                
                if row_errors:
                    for err_msg in row_errors:
                        error_messages.append(f"Error with {input.import_type} '{row_identifier}': {err_msg}")
                
                # If status is 'error' but no specific errors were in the list (should be rare)
                if status == 'error' and not row_errors:
                    error_messages.append(f"Unknown error processing {input.import_type} '{row_identifier}'.")

            except Exception as e_row: # Catch unexpected errors from a handler.handle call or product lookup
                error_messages.append(f"Critical error processing {input.import_type} '{row_identifier}': {str(e_row)}")
        
        final_error_count = len(error_messages)

        # Optional: Rollback if there are any errors and you want strict atomicity
        # if final_error_count > 0:
        #     transaction.set_rollback(True) # This will only work if an exception is raised to trigger rollback
        #     # To ensure rollback with custom error handling like this, you might need to raise an exception
        #     # at the end if final_error_count > 0, which will then be caught by Django's transaction management.
        #     # For now, we are committing even if there are non-critical errors per row.
        #     # If strict rollback is needed, this part needs adjustment.
        #     return cls(
        #         success=False, # Mark as not successful
        #         imported_count=0, updated_count=0, skipped_count=0, # Reset counts as it's rolled back
        #         error_count=final_error_count, 
        #         errors=["Import failed and was rolled back due to errors."] + error_messages
        #     )

        return cls(
            success=final_error_count == 0, # Overall success if no errors were reported
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            error_count=final_error_count,
            errors=error_messages
        )

class ProductImportExportMutations(graphene.ObjectType):
    import_data = ImportDataMutation.Field()
    # export_data = ExportDataMutation.Field() # Assuming ExportDataMutation is defined
