# customers/schema.py
import graphene
from .queries import CustomerQueries
from .mutations import CustomerMutations

class Query(CustomerQueries, graphene.ObjectType):
    pass

class Mutation(CustomerMutations, graphene.ObjectType):
    pass