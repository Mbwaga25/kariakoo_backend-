# ads/graphql/schema.py

import graphene
from .queries import AdsQuery
from .mutation import CreateAd, UpdateAd, DeleteAd

class Query(AdsQuery, graphene.ObjectType):
    pass

class Mutation(graphene.ObjectType):
    create_ad = CreateAd.Field()
    update_ad = UpdateAd.Field()
    delete_ad = DeleteAd.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
