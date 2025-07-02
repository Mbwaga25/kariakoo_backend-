# customers/queries.py
import graphene
from .schema_types import AddressType
from .models import Address
from graphql_jwt.decorators import login_required # For protecting queries

class CustomerQueries(graphene.ObjectType):
    my_addresses = graphene.List(AddressType)
    address_by_id = graphene.Field(AddressType, id=graphene.ID(required=True))

    @login_required
    def resolve_my_addresses(self, info):
        user = info.context.user
        return Address.objects.filter(user=user)

    @login_required
    def resolve_address_by_id(self, info, id):
        user = info.context.user
        try:
            return Address.objects.get(pk=id, user=user) # Ensure user owns the address
        except Address.DoesNotExist:
            return None