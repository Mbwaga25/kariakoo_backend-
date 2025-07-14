import graphene
from ..models import ProductVendor
from ..types.vendor import ProductVendorType

class ProductVendorQuery(graphene.ObjectType):
    all_product_vendors = graphene.List(ProductVendorType)

    def resolve_all_product_vendors(self, info):
        return ProductVendor.objects.all()
