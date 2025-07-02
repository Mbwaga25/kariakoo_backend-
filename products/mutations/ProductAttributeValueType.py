import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import login_required  # Assuming you might want this

# --- Assumed Imports from your project ---
from ..models import Product, Attribute, ProductAttributeValue
from ..types import ProductAttributeValueType # The type that represents the model

# 1. Input Object Type for the mutations
# This defines the data structure for creating or updating a ProductAttributeValue.
class ProductAttributeValueInput(graphene.InputObjectType):
    product_id = graphene.ID(required=True, description="The ID of the product.")
    attribute_id = graphene.ID(required=True, description="The ID of the attribute (e.g., 'Color', 'Size').")
    value = graphene.String(required=True, description="The specific value for the attribute (e.g., 'Red', 'XL').")


# 2. CREATE Mutation
class CreateProductAttributeValueMutation(graphene.Mutation):
    class Arguments:
        input = ProductAttributeValueInput(required=True)

    # Output fields
    product_attribute_value = graphene.Field(ProductAttributeValueType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required  # Uncomment to protect this mutation
    def mutate(cls, root, info, input):
        try:
            # Check if the related objects exist
            product = Product.objects.get(pk=input.product_id)
            attribute = Attribute.objects.get(pk=input.attribute_id)
            
            # Create the instance
            instance = ProductAttributeValue(
                product=product,
                attribute=attribute,
                value=input.value
            )

            # Run Django's model validation
            instance.full_clean()
            instance.save()
            
            return cls(product_attribute_value=instance, success=True, errors=[])

        except (Product.DoesNotExist, Attribute.DoesNotExist) as e:
            return cls(product_attribute_value=None, success=False, errors=["Product or Attribute not found."])
        except ValidationError as e:
            # Catches validation errors, like a unique_together constraint violation
            return cls(product_attribute_value=None, success=False, errors=list(e.messages))
        except Exception as e:
            # Generic catch-all for other errors
            return cls(product_attribute_value=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 3. UPDATE Mutation
# The input for an update only requires the value, as the product/attribute link is fixed.
class UpdateProductAttributeValueInput(graphene.InputObjectType):
     value = graphene.String(required=True, description="The new value for the attribute.")

class UpdateProductAttributeValueMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="The ID of the ProductAttributeValue record to update.")
        input = UpdateProductAttributeValueInput(required=True)
    
    # Output fields
    product_attribute_value = graphene.Field(ProductAttributeValueType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required  # Uncomment to protect this mutation
    def mutate(cls, root, info, id, input):
        try:
            # Find the specific record to update
            instance = ProductAttributeValue.objects.get(pk=id)
            
            # Update the value
            instance.value = input.value
            
            # Run validation and save
            instance.full_clean()
            instance.save()
            
            return cls(product_attribute_value=instance, success=True, errors=[])
        
        except ProductAttributeValue.DoesNotExist:
            return cls(product_attribute_value=None, success=False, errors=["Record not found."])
        except ValidationError as e:
            return cls(product_attribute_value=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(product_attribute_value=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 4. DELETE Mutation
class DeleteProductAttributeValueMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        
    # Output fields
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id):
        try:
            instance = ProductAttributeValue.objects.get(pk=id)
            instance.delete()
            return cls(success=True, errors=[])

        except ProductAttributeValue.DoesNotExist:
            return cls(success=False, errors=["Record not found."])
        except Exception as e:
            return cls(success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 5. Add to your root Mutation class
class Mutation(graphene.ObjectType):
    create_product_attribute_value = CreateProductAttributeValueMutation.Field()
    update_product_attribute_value = UpdateProductAttributeValueMutation.Field()
    delete_product_attribute_value = DeleteProductAttributeValueMutation.Field()

    # ... include your other mutations like CreateProductCategoryMutation here