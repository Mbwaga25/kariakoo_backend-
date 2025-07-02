# products/types/segment.py
import graphene
from graphene_django import DjangoObjectType
from ..models import ProductSegment

class ProductSegmentType(DjangoObjectType):
    # ✅ CORRECTED: Use a string path for the forward reference.
    products = graphene.List(graphene.NonNull("products.types.product.ProductType"))

    class Meta:
        model = ProductSegment
        fields = ("id", "title", "slug", "is_active", "order", "products")

    def resolve_products(self, info):
        return self.products.filter(is_globally_active=True).order_by("name")

# -------------------------------------------------
    