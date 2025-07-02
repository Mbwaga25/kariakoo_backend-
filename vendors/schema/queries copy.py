import graphene
from ..models import Vendor, ProductVendor, FoodVendor, ServiceProvider
from ..types.vendor import VendorType
from ..types.product import ProductVendorType
from ..types.food import FoodVendorType
from ..types.service import ServiceProviderType

class VendorsQuery(graphene.ObjectType):
    vendors = graphene.List(VendorType)
    vendor = graphene.Field(VendorType, id=graphene.ID())
    
    product_vendors = graphene.List(ProductVendorType)
    product_vendor = graphene.Field(ProductVendorType, id=graphene.ID())
    
    food_vendors = graphene.List(FoodVendorType)
    food_vendor = graphene.Field(FoodVendorType, id=graphene.ID())
    
    service_providers = graphene.List(ServiceProviderType)
    service_provider = graphene.Field(ServiceProviderType, id=graphene.ID())
    
    def resolve_vendors(self, info):
        return Vendor.objects.all()
    
    def resolve_vendor(self, info, id):
        return Vendor.objects.get(pk=id)
    
    def resolve_product_vendors(self, info):
        return ProductVendor.objects.all()
    
    def resolve_product_vendor(self, info, id):
        return ProductVendor.objects.get(pk=id)
    
    def resolve_food_vendors(self, info):
        return FoodVendor.objects.all()
    
    def resolve_food_vendor(self, info, id):
        return FoodVendor.objects.get(pk=id)
    
    def resolve_service_providers(self, info):
        return ServiceProvider.objects.all()
    
    def resolve_service_provider(self, info, id):
        return ServiceProvider.objects.get(pk=id)