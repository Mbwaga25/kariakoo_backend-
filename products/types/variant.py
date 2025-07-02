# products/types/variant.py
import graphene
from graphene_django import DjangoObjectType
from ..models import ProductVariant

class ProductVariantType(DjangoObjectType):
    class Meta:
        model = ProductVariant
        fields = ("id", "product", "name", "sku", "barcode", "additional_price", "is_active", "stock")

# -------------------------------------------------
