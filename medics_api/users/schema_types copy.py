# users/schema_types.py

import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from customers.models import Address

UserModel = get_user_model()


class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        interfaces = (graphene.relay.Node,)
        fields = [
            'id', 'full_name', 'phone_number', 'street_address',
            'delivery_notes', 'region', 'district', 'ward', 'village',
            'house_number', 'landmark', 'tin_number', 'business_name',
            'address_type', 'default', 'created_at', 'updated_at'
        ]
        filter_fields = {
            'region': ['exact', 'icontains'],
            'district': ['exact', 'icontains'],
            'ward': ['exact', 'icontains'],
            'address_type': ['exact'],
            'default': ['exact'],
        }


class UserType(DjangoObjectType):
    addresses = graphene.List(AddressType)

    class Meta:
        model = UserModel
        interfaces = (graphene.relay.Node,)
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login'
        ]
        filter_fields = {
            'username': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'is_active': ['exact'],
            'is_staff': ['exact'],
        }

    def resolve_addresses(self, info):
        return self.addresses.all()


class UserConnection(graphene.relay.Connection):
    class Meta:
        node = UserType
