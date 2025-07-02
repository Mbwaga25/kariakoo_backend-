# stores/schema.py
import graphene
from .queries import StoreQueries
from .mutations import StoreManagementMutations

class Query(StoreQueries, graphene.ObjectType):
    pass

class Mutation(StoreManagementMutations, graphene.ObjectType):
    pass