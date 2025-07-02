import graphene
from graphql_jwt.decorators import staff_member_required
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from products.models import ProductSegment, Product
from products.types import ProductSegmentType
from .inputs import ProductSegmentInput


class CreateProductSegmentMutation(graphene.Mutation):
    class Arguments:
        input = ProductSegmentInput(required=True)

    segment = graphene.Field(ProductSegmentType)
    success = graphene.Boolean(required=True)
    errors = graphene.List(graphene.NonNull(graphene.String))

    @classmethod
    @staff_member_required
    def mutate(cls, root, info, input):
        try:
            segment = ProductSegment.objects.create(
                title=input.title,
                slug=input.slug or slugify(input.title),
                order=input.order if input.order is not None else 0,
                is_active=input.is_active if input.is_active is not None else True
            )
            if input.product_ids:
                products = Product.objects.filter(id__in=input.product_ids)
                segment.products.set(products)

            return cls(segment=segment, success=True, errors=[])

        except ValidationError as e:
            return cls(segment=None, success=False, errors=e.messages)
        except Exception as e:
            return cls(segment=None, success=False, errors=[str(e)])


class UpdateProductSegmentMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ProductSegmentInput(required=True)

    segment = graphene.Field(ProductSegmentType)
    success = graphene.Boolean(required=True)
    errors = graphene.List(graphene.NonNull(graphene.String))

    @classmethod
    @staff_member_required
    def mutate(cls, root, info, id, input):
        try:
            segment = ProductSegment.objects.get(pk=id)
            segment.title = input.title
            segment.slug = input.slug or slugify(input.title)
            segment.order = input.order if input.order is not None else segment.order
            segment.is_active = input.is_active if input.is_active is not None else segment.is_active
            segment.save()

            if input.product_ids is not None:
                products = Product.objects.filter(id__in=input.product_ids)
                segment.products.set(products)

            return cls(segment=segment, success=True, errors=[])

        except ProductSegment.DoesNotExist:
            return cls(segment=None, success=False, errors=["Product segment not found."])
        except ValidationError as e:
            return cls(segment=None, success=False, errors=e.messages)
        except Exception as e:
            return cls(segment=None, success=False, errors=[str(e)])


class DeleteProductSegmentMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean(required=True)
    errors = graphene.List(graphene.NonNull(graphene.String))

    @classmethod
    @staff_member_required
    def mutate(cls, root, info, id):
        try:
            segment = ProductSegment.objects.get(pk=id)
            segment.delete()
            return cls(success=True, errors=[])

        except ProductSegment.DoesNotExist:
            return cls(success=False, errors=["Product segment not found."])
        except Exception as e:
            return cls(success=False, errors=[str(e)])
