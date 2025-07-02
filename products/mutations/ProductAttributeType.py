import graphene
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import login_required # For authentication

# --- Assumed Imports from your project ---
from ..models import Attribute
from ..types import AttributeType # Your provided AttributeType

# 1. Input Object Type for the mutations
# This defines the data structure for creating or updating an Attribute.
class AttributeInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="The name of the attribute (e.g., 'Color', 'Storage').")
    slug = graphene.String(description="Optional URL-friendly slug. If not provided, it will be generated from the name.")


# 2. CREATE Mutation
class CreateAttributeMutation(graphene.Mutation):
    class Arguments:
        input = AttributeInput(required=True)

    # Output fields
    attribute = graphene.Field(AttributeType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, input):
        try:
            # Create the Attribute instance
            instance = Attribute(
                name=input.name,
                # If a slug is provided, use it; otherwise, generate it from the name
                slug=input.slug or slugify(input.name)
            )

            # Run Django's model validation (e.g., checks for unique constraints)
            instance.full_clean()
            instance.save()
            
            return cls(attribute=instance, success=True, errors=[])

        except ValidationError as e:
            # Catches validation errors, like a non-unique name or slug
            return cls(attribute=None, success=False, errors=list(e.messages))
        except Exception as e:
            # Generic catch-all for other unexpected errors
            return cls(attribute=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 3. UPDATE Mutation
class UpdateAttributeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="The ID of the Attribute to update.")
        # We reuse the same input, but the logic will handle partial updates
        input = AttributeInput(required=True)
    
    # Output fields
    attribute = graphene.Field(AttributeType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id, input):
        try:
            # Find the specific Attribute record to update
            instance = Attribute.objects.get(pk=id)
            
            # Update the fields
            instance.name = input.name
            instance.slug = input.slug or slugify(input.name) # Recalculate slug if name changes or if slug is provided
            
            # Run validation and save the changes
            instance.full_clean()
            instance.save()
            
            return cls(attribute=instance, success=True, errors=[])
        
        except Attribute.DoesNotExist:
            return cls(attribute=None, success=False, errors=["Attribute not found."])
        except ValidationError as e:
            return cls(attribute=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(attribute=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 4. DELETE Mutation
class DeleteAttributeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        
    # Output fields
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id):
        try:
            instance = Attribute.objects.get(pk=id)
            instance.delete()
            return cls(success=True, errors=[])

        except Attribute.DoesNotExist:
            return cls(success=False, errors=["Attribute not found."])
        except Exception as e:
            # This can catch ProtectedError if the attribute is in use and protected by a ForeignKey
            return cls(success=False, errors=[f"An unexpected error occurred: {str(e)}"])


