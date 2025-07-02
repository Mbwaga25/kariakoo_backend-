import graphene
from ..types.vendor import VendorType
from ..models import Vendor

class VendorQuery(graphene.ObjectType):
    vendors = graphene.List(VendorType)
    vendor = graphene.Field(VendorType, id=graphene.ID())

    def resolve_vendors(self, info):
        return Vendor.objects.all()

    def resolve_vendor(self, info, id):
        return Vendor.objects.get(pk=id)
