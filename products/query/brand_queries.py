import graphene
from ..models import Brand
from ..types import BrandType


class BrandFilterInput(graphene.InputObjectType):
    name_contains = graphene.String()


class BrandQueries(graphene.ObjectType):
    all_brands = graphene.List(
        graphene.NonNull(BrandType),
        filter=BrandFilterInput(),
        sort_by=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int(),
        description="Retrieve all product brands with filtering, sorting, and pagination"
    )

    brand = graphene.Field(
        BrandType,
        id=graphene.ID(required=False),
        slug=graphene.String(required=False),
        description="Retrieve a single brand by ID or slug"
    )

    def resolve_all_brands(self, info, filter=None, sort_by=None, limit=None, offset=None, **kwargs):
        queryset = Brand.objects.all()

        if filter and filter.name_contains:
            queryset = queryset.filter(name__icontains=filter.name_contains)

        if sort_by:
            queryset = queryset.order_by(sort_by)
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]

        return queryset

    def resolve_brand(self, info, id=None, slug=None):
        if id:
            return Brand.objects.filter(id=id).first()
        if slug:
            return Brand.objects.filter(slug=slug).first()
        return None
