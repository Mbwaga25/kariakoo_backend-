# products/types/tag.py
import graphene
from graphene_django import DjangoObjectType
from ..models import Tag

class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")

# -------------------------------------------------
