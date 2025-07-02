# order_call/graphql/queries.py

import graphene
from ..models import OrderCallRequest
from .types import OrderCallRequestType
from graphql import GraphQLError

class Query(graphene.ObjectType):
    # Query to fetch all order call requests
    all_order_call_requests = graphene.List(OrderCallRequestType)

    # Query to fetch a single order call request by its ID
    order_call_request_by_id = graphene.Field(
        OrderCallRequestType, 
        id=graphene.UUID(required=True)
    )

    def resolve_all_order_call_requests(self, info):
        """
        Returns all order call requests.
        SECURITY: Only accessible by staff users.
        """
        if not info.context.user.is_staff:
            raise GraphQLError("You do not have permission to perform this action.")
        return OrderCallRequest.objects.all().prefetch_related('files')

    def resolve_order_call_request_by_id(self, info, id):
        """
        Returns a single order call request by its UUID.
        SECURITY: Only accessible by staff users.
        """
        if not info.context.user.is_staff:
            raise GraphQLError("You do not have permission to perform this action.")
            
        try:
            return OrderCallRequest.objects.get(pk=id)
        except OrderCallRequest.DoesNotExist:
            return None