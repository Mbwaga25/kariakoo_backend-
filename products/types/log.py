# products/types/log.py
import graphene

class LogProductViewType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()