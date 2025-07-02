# -------------------------------------------------

# products/types/attribute.py
import graphene
from graphene_django import DjangoObjectType
from ..models import Attribute

class AttributeType(DjangoObjectType):
    class Meta:
        model = Attribute
        fields = ("id", "name", "slug")

# -------------------------------------------------
