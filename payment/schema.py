import graphene
from .queries import PaymentQuery
from .mutations import PaymentMutation
schema = graphene.Schema(query=PaymentQuery, mutation=PaymentMutation)