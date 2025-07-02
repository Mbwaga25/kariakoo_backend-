
# products/types/brand.py
import graphene
from graphene_django import DjangoObjectType
from ..models import Brand

class BrandType(DjangoObjectType):
    products = graphene.List("products.types.product.ProductType")

    class Meta:
        model = Brand
        fields = ("id", "name", "slug", "logo", "description", "products")

    def resolve_products(self, info):
        return self.products.filter(is_globally_active=True)

# -------------------------------------------------