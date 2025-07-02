import graphene
from ..types.product import ProductVendorType
from ..models import ProductVendor

class ProductQuery(graphene.ObjectType):
    product_vendors = graphene.List(ProductVendorType)
    product_vendor = graphene.Field(ProductVendorType, id=graphene.ID())

    def resolve_product_vendors(self, info):
        return ProductVendor.objects.all()

    def resolve_product_vendor(self, info, id):
        return ProductVendor.objects.get(pk=id)
