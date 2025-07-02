import graphene
from graphene_django import DjangoObjectType
from ..models import Vendor

class VendorType(DjangoObjectType):
    class Meta:
        model = Vendor
        fields = '__all__'

class AuthPayload(graphene.ObjectType):
    token = graphene.String()
    vendor = graphene.Field(VendorType)