import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import login_required

# --- Assumed Imports from your project ---
from ..models import Product, ProductVariant
from ..types import ProductVariantType # Your provided ProductVariantType

# 1. Input Object Type for the mutations
# Defines the data needed to create or update a ProductVariant.
class ProductVariantInput(graphene.InputObjectType):
    product_id = graphene.ID(required=True, description="The ID of the parent product.")
    name = graphene.String(required=True, description="The name of the variant (e.g., 'Red / Large').")
    sku = graphene.String(description="Stock Keeping Unit. Should be unique.", required=True)
    barcode = graphene.String(description="Barcode (GTIN, UPC, etc.).")
    additional_price = graphene.Decimal(description="Price difference from the base product price.", default_value=0)
    is_active = graphene.Boolean(description="Whether this variant is available for purchase.", default_value=True)
    stock = graphene.Int(description="The number of items in stock.", default_value=0)


# 2. CREATE Mutation
class CreateProductVariantMutation(graphene.Mutation):
    class Arguments:
        input = ProductVariantInput(required=True)

    # Output fields
    product_variant = graphene.Field(ProductVariantType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, input):
        try:
            # Find the parent product
            product = Product.objects.get(pk=input.product_id)
            
            # Create the ProductVariant instance
            instance = ProductVariant(
                product=product,
                name=input.name,
                sku=input.sku,
                barcode=input.barcode,
                additional_price=input.additional_price,
                is_active=input.is_active,
                stock=input.stock
            )

            # Run Django's model validation (checks for unique SKU, etc.)
            instance.full_clean()
            instance.save()
            
            return cls(product_variant=instance, success=True, errors=[])

        except Product.DoesNotExist:
            return cls(product_variant=None, success=False, errors=["Parent product not found."])
        except ValidationError as e:
            return cls(product_variant=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(product_variant=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 3. UPDATE Mutation
class UpdateProductVariantMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="The ID of the ProductVariant to update.")
        input = ProductVariantInput(required=True)
    
    # Output fields
    product_variant = graphene.Field(ProductVariantType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id, input):
        try:
            instance = ProductVariant.objects.get(pk=id)
            
            # Update the fields from the input.
            # Note: We intentionally do not update the parent product_id,
            # as moving a variant between products is typically not a standard operation.
            instance.name = input.name
            instance.sku = input.sku
            instance.barcode = input.barcode if input.barcode is not None else instance.barcode
            instance.additional_price = input.additional_price
            instance.is_active = input.is_active
            instance.stock = input.stock
            
            instance.full_clean()
            instance.save()
            
            return cls(product_variant=instance, success=True, errors=[])
        
        except ProductVariant.DoesNotExist:
            return cls(product_variant=None, success=False, errors=["ProductVariant not found."])
        except ValidationError as e:
            return cls(product_variant=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(product_variant=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 4. DELETE Mutation
class DeleteProductVariantMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        
    # Output fields
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id):
        try:
            instance = ProductVariant.objects.get(pk=id)
            instance.delete()
            return cls(success=True, errors=[])

        except ProductVariant.DoesNotExist:
            return cls(success=False, errors=["ProductVariant not found."])
        except Exception as e:
            return cls(success=False, errors=[f"An unexpected error occurred: {str(e)}"])

