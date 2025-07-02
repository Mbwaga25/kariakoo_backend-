import graphene
from graphene_django import DjangoObjectType
from ..models import FoodVendor

class FoodVendorType(DjangoObjectType):
    class Meta:
        model = FoodVendor
        fields = '__all__'