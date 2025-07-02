import graphene
from ..models import Tag
from ..types import TagType, ProductType
from .base import BaseProductQueries

class TagQueries(BaseProductQueries):
    """Tag-related GraphQL queries"""
    
    all_tags = graphene.List(
        graphene.NonNull(TagType),
        description="Retrieve all product tags."
    )
    
    products_by_tag_slug = graphene.List(
        graphene.NonNull(ProductType),
        tag_slug=graphene.String(required=True),
        description="Retrieve products by tag slug."
    )

    def resolve_all_tags(self, info, **kwargs):
        return Tag.objects.all()

    def resolve_products_by_tag_slug(self, info, tag_slug, **kwargs):
        try:
            tag = Tag.objects.get(slug=tag_slug)
            return self.get_product_queryset().filter(tags=tag)
        except Tag.DoesNotExist:
            return Product.objects.none()