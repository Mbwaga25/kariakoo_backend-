# your_app/products/import_export.py
import graphene
from django.db import transaction
from .inputs import ImportInput, ExportInput # Adjusted path to shared inputs
from .helpers import process_csv_file, process_json_file # Adjusted path to shared helpers
from ..models import Product # Assuming models.py is at the app root (e.g., your_app/models.py)

# Import all handlers from the shared product_import_export/handlers directory
from .handlers.brand_handler import BrandHandler
from .handlers.category_handler import CategoryHandler
from .handlers.attribute_handler import AttributeHandler
from .handlers.tag_handler import TagHandler
from .handlers.product_handler import ProductHandler
from .handlers.product_image_handler import ProductImageHandler
from .handlers.product_variant_handler import ProductVariantHandler
from .handlers.product_segment_handler import ProductSegmentHandler
# Note: BaseHandler is not directly used in the handler_map but is a parent for others.

class ImportDataMutation(graphene.Mutation):
    class Arguments:
        input = ImportInput(required=True)

    success = graphene.NonNull(graphene.Boolean)
    imported_count = graphene.Int(default_value=0)
    updated_count = graphene.Int(default_value=0)
    skipped_count = graphene.Int(default_value=0)
    error_count = graphene.Int(default_value=0)
    errors = graphene.List(graphene.NonNull(graphene.String))

    @classmethod
    # @staff_member_required # Add your authentication/authorization if using product_import_export_jwt
    @transaction.atomic
    def mutate(cls, root, info, input: ImportInput):
        handler_map = {
            'brand': BrandHandler,
            'category': CategoryHandler,
            'attribute': AttributeHandler,
            'tag': TagHandler,
            'product': ProductHandler,
            'productimage': ProductImageHandler,
            'variant': ProductVariantHandler,
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
            return cls(success=True, errors=["No data found in file to import."], skipped_count=0)

        handler_instance = HandlerClass(
            update_existing=input.update_existing,
            create_related=input.create_related
        )

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_messages = []

        for idx, row_data in enumerate(data_rows):
            row_identifier_key = getattr(handler_instance, 'lookup_field', 'name')
            if isinstance(row_identifier_key, list):
                row_identifier_key = row_identifier_key[0]
            row_identifier = row_data.get(row_identifier_key, f"Row {idx+1}")

            try:
                result = None
                if HandlerClass in [ProductImageHandler, ProductVariantHandler]:
                    product_ref_val = row_data.get('product_name') or row_data.get('product_id')
                    product_ref_key = 'name' if row_data.get('product_name') else 'id'

                    if not product_ref_val:
                        error_messages.append(f"Missing 'product_name' or 'product_id' for {import_type_lower} '{row_identifier}'.")
                        continue

                    try:
                        parent_product = Product.objects.get(**{product_ref_key: product_ref_val})
                    except Product.DoesNotExist:
                        error_messages.append(f"Parent Product '{product_ref_val}' not found for {import_type_lower} '{row_identifier}'.")
                        continue
                    except Product.MultipleObjectsReturned:
                        error_messages.append(f"Multiple Parent Products found for '{product_ref_val}' for {import_type_lower} '{row_identifier}'.")
                        continue
                    result = handler_instance.handle(row_data, product_instance=parent_product)
                else:
                    result = handler_instance.handle(row_data)
                
                status = result.get('status')
                row_errors = result.get('errors', [])

                if status == 'created':
                    imported_count += 1
                elif status == 'updated':
                    updated_count += 1
                elif status == 'skipped':
                    skipped_count += 1
                elif status == 'completed_with_errors':
                    updated_count += 1 # Or decide based on primary action
                elif status == 'skipped_with_errors':
                    skipped_count +=1
                
                if row_errors:
                    for err_msg in row_errors:
                        error_messages.append(f"Error with {input.import_type} '{row_identifier}': {err_msg}")
                if status == 'error' and not row_errors:
                    error_messages.append(f"Unknown error processing {input.import_type} '{row_identifier}'.")

            except Exception as e_row:
                error_messages.append(f"Critical error processing {input.import_type} '{row_identifier}': {str(e_row)}")
        
        final_error_count = len(error_messages)
        return cls(
            success=final_error_count == 0,
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            error_count=final_error_count,
            errors=error_messages
        )

class ExportDataMutation(graphene.Mutation): # Placeholder from your example
    class Arguments:
        # Define arguments for export if needed
        input = ExportInput(required=True) # Assuming ExportInput is defined in ..product_import_export.inputs

    success = graphene.NonNull(graphene.Boolean)
    file_content = graphene.String() # Base64 encoded string or similar
    errors = graphene.List(graphene.NonNull(graphene.String))

    @classmethod
    # @staff_member_required
    def mutate(cls, root, info, input):
        # Implement export logic here based on input.export_type and input.format
        # This is a placeholder
        return cls(success=False, errors=["Export functionality not yet implemented."])


class ProductImportExportMutations(graphene.ObjectType):
    import_data = ImportDataMutation.Field()
    export_data = ExportDataMutation.Field() # Add if you have an ExportDataMutation
