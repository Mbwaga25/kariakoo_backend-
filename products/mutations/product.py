import graphene
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import login_required
import graphene_file_upload.scalars
from ..models import Product, ProductCategory, Brand, Tag, ProductImage
from ..types import ProductType

# Input Type
class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    slug = graphene.String()
    description = graphene.String()
    category_id = graphene.ID(required=True)
    brand_id = graphene.ID(required=True)
    tag_ids = graphene.List(graphene.NonNull(graphene.ID))
    price = graphene.Decimal(required=True)
    is_globally_active = graphene.Boolean(default_value=True)
    meta_title = graphene.String()
    meta_description = graphene.String()
    images = graphene.List(graphene_file_upload.scalars.Upload, required=False)


# CREATE Mutation
class CreateProductMutation(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        try:
            category = ProductCategory.objects.get(pk=input.category_id)
            brand = Brand.objects.get(pk=input.brand_id)

            instance = Product(
                name=input.name,
                slug=input.slug or slugify(input.name),
                description=input.description,
                category=category,
                brand=brand,
                price=input.price,
                is_globally_active=input.is_globally_active,
                meta_title=input.meta_title,
                meta_description=input.meta_description
            )
            instance.full_clean()
            instance.save()

            # Handle tags
            if input.tag_ids:
                tags = Tag.objects.filter(pk__in=input.tag_ids)
                instance.tags.set(tags)

            # Handle images
            # image_files = input.images or []
            # for i, image_file in enumerate(image_files):
            #     image_instance = ProductImage(
            #         product=instance,
            #         image=image_file,
            #         alt_text=f"{instance.name} - Image {i + 1}",
            #         order=i
            #     )
            #     if not instance.images.filter(is_primary=True).exists() and i == 0:
            #         image_instance.is_primary = True
            #     image_instance.save()

            return cls(product=instance, success=True, errors=[])

        except (ProductCategory.DoesNotExist, Brand.DoesNotExist):
            return cls(product=None, success=False, errors=["Category or Brand not found."])
        except ValidationError as e:
            return cls(product=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(product=None, success=False, errors=[f"Unexpected error: {str(e)}"])


# UPDATE Mutation
class UpdateProductMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, id, input):
        try:
            instance = Product.objects.get(pk=id)

            instance.name = input.name
            instance.slug = input.slug or slugify(input.name)
            instance.description = input.description
            instance.price = input.price
            instance.is_globally_active = input.is_globally_active
            instance.meta_title = input.meta_title
            instance.meta_description = input.meta_description

            if input.category_id:
                instance.category = ProductCategory.objects.get(pk=input.category_id)
            if input.brand_id:
                instance.brand = Brand.objects.get(pk=input.brand_id)

            if input.tag_ids is not None:
                tags = Tag.objects.filter(pk__in=input.tag_ids)
                instance.tags.set(tags)

            instance.full_clean()
            instance.save()

            # Handle new image uploads
            image_files = input.images or []
            if image_files:
                has_primary = instance.images.filter(is_primary=True).exists()
                for i, image_file in enumerate(image_files):
                    image_instance = ProductImage(
                        product=instance,
                        image=image_file,
                        alt_text=f"{instance.name} - New Image {i + 1}",
                        order=instance.images.count() + i
                    )
                    if not has_primary and i == 0:
                        image_instance.is_primary = True
                    image_instance.save()

            return cls(product=instance, success=True, errors=[])

        except Product.DoesNotExist:
            return cls(product=None, success=False, errors=["Product not found."])
        except (ProductCategory.DoesNotExist, Brand.DoesNotExist):
            return cls(product=None, success=False, errors=["Category or Brand not found."])
        except ValidationError as e:
            return cls(product=None, success=False, errors=list(e.messages))
        except Exception as e:
            return cls(product=None, success=False, errors=[f"Unexpected error: {str(e)}"])


# DELETE Mutation
class DeleteProductMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, id):
        try:
            instance = Product.objects.get(pk=id)
            instance.delete()
            return cls(success=True, errors=[])
        except Product.DoesNotExist:
            return cls(success=False, errors=["Product not found."])
        except Exception as e:
            return cls(success=False, errors=[f"Unexpected error: {str(e)}"])
