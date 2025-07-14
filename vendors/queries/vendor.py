import graphene
from ..models import Vendor
from ..types.vendor import VendorType

class VendorQuery(graphene.ObjectType):
    all_vendors = graphene.List(VendorType)
    all_product_vendors = graphene.List(VendorType)
    all_sponsor_vendors = graphene.List(VendorType)
    all_vendor_vendors = graphene.List(VendorType)  # ✅ Added for vendor type 'vendor'

    def resolve_all_vendors(self, info):
        return Vendor.objects.all().order_by('-registration_date')

    def resolve_all_product_vendors(self, info):
        return Vendor.objects.filter(vendor_type='product').order_by('-registration_date')

 
    def resolve_all_sponsor_vendors(self, info):
        return Vendor.objects.filter(vendor_type='sponsor').order_by('-registration_date')

    def resolve_all_vendor_vendors(self, info):
        return Vendor.objects.filter(vendor_type='vendor').order_by('-registration_date')  # ✅ For 'vendor' type
