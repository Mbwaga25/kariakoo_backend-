import graphene
from .query import ProductCatalogQueries
from .mutations import ProductCatalogMutations  # Now includes create_product_segment

class Query(ProductCatalogQueries, graphene.ObjectType):
    pass

class Mutation(ProductCatalogMutations, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
