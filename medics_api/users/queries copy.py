# users/queries.py
import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .schema_types import UserType, AddressType
from customers.models import Address
from graphql_jwt.decorators import login_required
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField


UserModel = get_user_model()

class UserProfileQueries(graphene.ObjectType):
    # Current authenticated user
    me = graphene.Field(
        UserType,
        description="Get current authenticated user's profile"
    )

    # User by ID (using Relay Node Field for global IDs)
    user = relay.Node.Field(
        UserType,
        description="Get user by global ID (restricted to admins or the user themselves)"
    )

    # List of all users with filtering and pagination (admin only)
    all_users = DjangoFilterConnectionField(
        UserType,
        description="List all users (admin only)",
    )

    # Current user's addresses
    my_addresses = graphene.List(
        AddressType,
        description="Get current user's addresses"
    )

    # Address by ID (must belong to current user, using Relay Node Field)
    address = relay.Node.Field(
        AddressType,
        description="Get specific address by global ID (must belong to current user)"
    )

    # Filterable list of addresses for the current user
    addresses = DjangoFilterConnectionField(
        AddressType,
        description="Get current user's addresses with filtering and pagination",
    )

    @login_required
    def resolve_me(self, info):
        """Get the currently authenticated user's profile."""
        return info.context.user

    @login_required
    def resolve_user(self, info, id):
        """
        Get a user by ID.
        Restricted to admins or the user themselves.
        """
        try:
            requested_user = UserModel.objects.get(pk=id)
            requesting_user = info.context.user
            
            if not (requesting_user.is_staff or requesting_user.pk == requested_user.pk):
                raise PermissionDenied("You don't have permission to view this user.")

            return requested_user
        except UserModel.DoesNotExist:
            return None
        except ValueError:
            return None

    @login_required
    def resolve_all_users(self, info, **kwargs):
        """List all users (admin only)."""
        if not info.context.user.is_staff:
            raise PermissionDenied("Only admin users can list all users.")
        return UserModel.objects.all()

    @login_required
    def resolve_my_addresses(self, info):
        """Get all addresses for the current user."""
        return Address.objects.filter(
            user=info.context.user
        ).order_by('-default', 'address_type')

    @login_required
    def resolve_address(self, info, id):
        """
        Get a specific address by ID.
        Must belong to the current user.
        """
        try:
            return Address.objects.get(id=id, user=info.context.user)
        except Address.DoesNotExist:
            return None
        except ValueError:
            return None

    @login_required
    def resolve_addresses(self, info, **kwargs):
        """Get filterable list of addresses for current user."""
        return Address.objects.filter(user=info.context.user)