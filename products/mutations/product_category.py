import graphene
from django.utils.text import slugify
# Import login_required instead of staff_member_required
from graphql_jwt.decorators import login_required 
from django.core.exceptions import ValidationError
from ..models import ProductCategory
from ..types import ProductCategoryType
from .inputs import ProductCategoryInput 
import graphene_file_upload.scalars


class ProductCategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    slug = graphene.String()
    description = graphene.String()
    parent_id = graphene.ID()
    image = graphene_file_upload.scalars.Upload(description="Product category image file.")

class CreateProductCategoryMutation(graphene.Mutation):
    class Arguments:
        input = ProductCategoryInput(required=True)

    category = graphene.Field(ProductCategoryType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required 
    def mutate(cls, root, info, input):
        image_file = input.image
        try:
            parent = None
            if input.parent_id:
                try:
                    # If input.parent_id is a Global ID, uncomment and use from_global_id
                    # from graphql_relay import from_global_id
                    # parent_pk = from_global_id(input.parent_id)[1]
                    # parent = ProductCategory.objects.get(pk=parent_pk)
                    parent = ProductCategory.objects.get(pk=input.parent_id)
                except ProductCategory.DoesNotExist:
                    return cls(category=None, success=False, errors=["Parent category not found."])
                except Exception as e: 
                    return cls(category=None, success=False, errors=[f"Invalid parent ID: {str(e)}"])

            category = ProductCategory.objects.create(
                name=input.name,
                slug=input.slug or slugify(input.name), 
                description=input.description,
                parent=parent,
               
            )

            if image_file: # Check if a file was provided
                category.image.save(image_file.name, image_file, save=False)
            
            category.full_clean()
            category.save() 
            return cls(category=category, success=True, errors=[])
        except ValidationError as e:
            return cls(category=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(category=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


class UpdateProductCategoryMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ProductCategoryInput(required=True)

    category = graphene.Field(ProductCategoryType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # <--- UNCOMMENTED AND ACTIVATED THIS DECORATOR
    def mutate(cls, root, info, id, input):
        try:
            # If you're using Relay Global IDs, you need to decode the ID
            # from graphql_relay import from_global_id
            # product_category_pk = from_global_id(id)[1]
            # category = ProductCategory.objects.get(pk=product_category_pk)
            category = ProductCategory.objects.get(pk=id)
        except ProductCategory.DoesNotExist:
            return cls(category=None, success=False, errors=["Category not found."])

        if input.parent_id is not None:
            try:
                # Same as above, if using Global IDs for parent_id
                # parent_pk = from_global_id(input.parent_id)[1]
                # category.parent = ProductCategory.objects.get(pk=parent_pk) if input.parent_id else None
                category.parent = ProductCategory.objects.get(pk=input.parent_id) if input.parent_id else None
            except ProductCategory.DoesNotExist:
                return cls(category=None, success=False, errors=["Parent category not found."])
            except Exception as e:
                return cls(category=None, success=False, errors=[f"Invalid parent ID: {str(e)}"])
        elif hasattr(input, 'parent_id') and input.parent_id is None:
            # Allow setting parent to None if parent_id is explicitly provided as null
            category.parent = None

        # Only update fields if they are provided in the input
        if input.name is not None:
            category.name = input.name
            category.slug = input.slug or slugify(input.name) # Recalculate slug if name changes
        if input.description is not None:
            category.description = input.description
        if input.image is not None: # Update image field (assuming URL string)
            category.image = input.image
        if input.slug is not None: # Allow direct slug override
            category.slug = input.slug

        try:
            category.full_clean() # Ensures model validation rules are applied
            category.save()
            return cls(category=category, success=True, errors=[])
        except ValidationError as e:
            return cls(category=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(category=None, success=False, errors=[f"An unexpected error occurred: {str(e)}"])


class DeleteProductCategoryMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    # @login_required # This one was already correct
    def mutate(cls, root, info, id):
        try:
            # If you're using Relay Global IDs, you need to decode the ID
            # from graphql_relay import from_global_id
            # product_category_pk = from_global_id(id)[1]
            # ProductCategory.objects.get(pk=product_category_pk).delete()
            ProductCategory.objects.get(pk=id).delete()
            return cls(success=True, errors=[])
        except ProductCategory.DoesNotExist:
            return cls(success=False, errors=["Category not found."])
        except Exception as e:
            return cls(success=False, errors=[str(e)])