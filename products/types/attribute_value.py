# products/types/attribute_value.py
import graphene
from graphene_django import DjangoObjectType
from django.utils.text import slugify
from ..models import ProductAttributeValue

class ProductAttributeValueType(DjangoObjectType):
    attribute_name = graphene.String()
    attribute_id = graphene.ID()
    value_slug = graphene.String()

    class Meta:
        model = ProductAttributeValue
        fields = ("id", "product", "attribute", "attribute_id", "attribute_name", "value")

    def resolve_attribute_name(self, info):
        return self.attribute.name

    def resolve_attribute_id(self, info):
        return self.attribute.id
    
    def resolve_value_slug(self, info):
        return slugify(self.value)

# -------------------------------------------------