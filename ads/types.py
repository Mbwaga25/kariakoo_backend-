from graphene_django import DjangoObjectType
from ads.models import Ad, Section, Page, AdAttributeValue
import graphene

class PageType(DjangoObjectType):
    class Meta:
        model = Page
        fields = ("id", "name")

class SectionType(DjangoObjectType):
    class Meta:
        model = Section
        fields = ("id", "name", "page")

class AdAttributeValueType(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()

class AdType(DjangoObjectType):
    attributes = graphene.List(AdAttributeValueType)

    class Meta:
        model = Ad
        fields = ("id", "title", "image", "link", "active", "section")

    def resolve_attributes(self, info):
        return [
            AdAttributeValueType(key=attr.attribute.name, value=attr.value)
            for attr in self.attributes.all()
        ]
