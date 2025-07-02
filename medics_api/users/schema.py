# schema.py
import graphene
from users.mutations import UserProfileMutations
from users.queries import UserProfileQueries


class Query(UserProfileQueries, graphene.ObjectType):
    pass


class Mutation(UserProfileMutations, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)