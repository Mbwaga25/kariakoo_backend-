# order_call/graphql/types.py

from graphene_django import DjangoObjectType
from ..models import OrderCallRequest

class OrderCallRequestType(DjangoObjectType):
    class Meta:
        model = OrderCallRequest
        fields = "__all__"