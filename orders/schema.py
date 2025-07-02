import graphene
from .mutations import OrderMutations
from .queries import Query as OrderQueries

class Query(OrderQueries, graphene.ObjectType):
    pass

class Mutation(OrderMutations, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
