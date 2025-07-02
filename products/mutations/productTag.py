import graphene
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import login_required

# --- Assumed Imports from your project ---
from ..models import Tag
from ..types import TagType # Your provided TagType

# 1. Input Object Type for the mutations
# Defines the data needed to create or update a Tag.
class TagInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="The name of the tag (e.g., 'Featured', 'New Arrival').")
    slug = graphene.String(description="Optional URL-friendly slug. If not provided, it's generated from the name.")


# 2. CREATE Mutation
class CreateTagMutation(graphene.Mutation):
    class Arguments:
        input = TagInput(required=True)

    # Output fields
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, input):
        try:
            # Create the Tag instance
            instance = Tag(
                name=input.name,
                slug=input.slug or slugify(input.name)
            )

            # Run Django's model validation
            instance.full_clean()
            instance.save()
            
            return cls(tag=instance, success=True, errors=[])

        except ValidationError as e:
            # Catches validation errors, like a non-unique name
            return cls(tag=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(tag=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 3. UPDATE Mutation
class UpdateTagMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="The ID of the Tag to update.")
        input = TagInput(required=True)
    
    # Output fields
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id, input):
        try:
            # Find the specific Tag record to update
            instance = Tag.objects.get(pk=id)
            
            # Update the fields
            instance.name = input.name
            instance.slug = input.slug or slugify(input.name)
            
            # Run validation and save
            instance.full_clean()
            instance.save()
            
            return cls(tag=instance, success=True, errors=[])
        
        except Tag.DoesNotExist:
            return cls(tag=None, success=False, errors=["Tag not found."])
        except ValidationError as e:
            return cls(tag=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(tag=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


# 4. DELETE Mutation
class DeleteTagMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        
    # Output fields
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # Uncomment to protect this mutation
    def mutate(cls, root, info, id):
        try:
            instance = Tag.objects.get(pk=id)
            instance.delete()
            return cls(success=True, errors=[])

        except Tag.DoesNotExist:
            return cls(success=False, errors=["Tag not found."])
        except Exception as e:
            return cls(success=False, errors=[f"An unexpected error occurred: {str(e)}"])


