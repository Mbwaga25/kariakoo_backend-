# food_service_queries.py
import graphene
from ..models import FoodVendor, ServiceProvider
from ..types.food import FoodVendorType
from ..types.service import ServiceProviderType

class FoodServiceQuery(graphene.ObjectType):
    food_vendors = graphene.List(FoodVendorType)
    food_vendor = graphene.Field(FoodVendorType, id=graphene.ID(required=True))
    service_providers = graphene.List(ServiceProviderType)
    service_provider = graphene.Field(ServiceProviderType, id=graphene.ID(required=True))

    def resolve_food_vendors(root, info):
        return FoodVendor.objects.all()

    def resolve_food_vendor(root, info, id):
        return FoodVendor.objects.get(pk=id)

    def resolve_service_providers(root, info):
        return ServiceProvider.objects.all()

    def resolve_service_provider(root, info, id):
        return ServiceProvider.objects.get(pk=id)
