# ads/graphql/queries.py

import graphene
from ads.models import Page, Section, Ad
from .types import AdType

class AdsQuery(graphene.ObjectType):
    all_ads = graphene.List(AdType)
    ads_by_page = graphene.List(AdType, page_name=graphene.String(required=True))
    ads_by_section = graphene.List(AdType, section_name=graphene.String(required=True))

    def resolve_all_ads(self, info):
        return Ad.objects.filter(active=True)

    def resolve_ads_by_page(self, info, page_name):
        try:
            page = Page.objects.get(name=page_name)
            return Ad.objects.filter(section__page=page, active=True)
        except Page.DoesNotExist:
            return []

    def resolve_ads_by_section(self, info, section_name):
        return Ad.objects.filter(section__name=section_name, active=True)
