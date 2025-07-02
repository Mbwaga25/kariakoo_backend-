# customers/schema_types.py
import graphene
from graphene_django import DjangoObjectType
from .models import Address
# If you also had a CustomerProfile model, import it here

class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        fields = "__all__"