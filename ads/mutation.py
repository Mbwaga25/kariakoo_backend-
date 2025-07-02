# ads/graphql/mutation.py

import graphene
from ads.models import Ad, Section, Attribute, AdAttributeValue
from .types import AdType

class CreateAd(graphene.Mutation):
    class Arguments:
        section_id = graphene.Int(required=True)
        title = graphene.String()
        image = graphene.String()
        link = graphene.String()
        active = graphene.Boolean()
        attributes = graphene.List(graphene.JSONString)

    ad = graphene.Field(AdType)

    def mutate(self, info, section_id, title=None, image=None, link=None, active=True, attributes=None):
        section = Section.objects.get(id=section_id)
        ad = Ad.objects.create(
            section=section, title=title, image=image, link=link, active=active
        )

        if attributes:
            for attr in attributes:
                key = attr.get("key")
                value = attr.get("value")
                attribute, _ = Attribute.objects.get_or_create(name=key)
                AdAttributeValue.objects.create(ad=ad, attribute=attribute, value=value)

        return CreateAd(ad=ad)

class UpdateAd(graphene.Mutation):
    class Arguments:
        ad_id = graphene.Int(required=True)
        title = graphene.String()
        image = graphene.String()
        link = graphene.String()
        active = graphene.Boolean()
        attributes = graphene.List(graphene.JSONString)

    ad = graphene.Field(AdType)

    def mutate(self, info, ad_id, title=None, image=None, link=None, active=None, attributes=None):
        ad = Ad.objects.get(id=ad_id)
        if title is not None:
            ad.title = title
        if image is not None:
            ad.image = image
        if link is not None:
            ad.link = link
        if active is not None:
            ad.active = active
        ad.save()

        if attributes:
            for attr in attributes:
                key = attr.get("key")
                value = attr.get("value")
                attribute, _ = Attribute.objects.get_or_create(name=key)
                attr_val, _ = AdAttributeValue.objects.get_or_create(ad=ad, attribute=attribute)
                attr_val.value = value
                attr_val.save()

        return UpdateAd(ad=ad)

class DeleteAd(graphene.Mutation):
    class Arguments:
        ad_id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, ad_id):
        Ad.objects.get(id=ad_id).delete()
        return DeleteAd(success=True)
