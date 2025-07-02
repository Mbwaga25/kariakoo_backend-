import graphene
from graphene_django import DjangoObjectType
from ..models import ServiceProvider

class ServiceProviderType(DjangoObjectType):
    class Meta:
        model = ServiceProvider
        fields = '__all__'