import graphene
from . vendor import RegisterVendor
from . product import RegisterProductVendor
from . food import RegisterFoodVendor
from . service import RegisterServiceProvider

class Mutation(graphene.ObjectType):
    register_vendor = RegisterVendor.Field()
    register_product_vendor = RegisterProductVendor.Field()
    register_food_vendor = RegisterFoodVendor.Field()
    register_service_provider = RegisterServiceProvider.Field()
