# users/mutations.py
import graphene
from django.contrib.auth import get_user_model
from customers.models import Address
from .schema_types import UserType, AddressType # Assuming UserType includes is_staff, is_superuser fields
from graphql_jwt.decorators import login_required
from graphql_jwt.shortcuts import get_token, get_refresh_token
from graphql_jwt import mutations as jwt_mutations
import graphql_jwt
from graphql_relay import from_global_id
from django.contrib.auth import authenticate
from graphql_jwt.shortcuts import create_refresh_token

UserModel = get_user_model()

# --- Input Types (No changes needed here) ---
class LoginUserInput(graphene.InputObjectType):
    """
    Input type for user login.
    Allows authentication using either username or email.
    """
    username_or_email = graphene.String(required=True, description="Username or email of the user.")
    password = graphene.String(required=True, description="Password of the user.")

class RegisterUserInput(graphene.InputObjectType):
    """
    Input type for new user registration.
    """
    username = graphene.String(required=True, description="Desired username for the new user.")
    password = graphene.String(required=True, description="Password for the new user.")
    email = graphene.String(required=True, description="Email address for the new user.")
    first_name = graphene.String(description="First name of the user (optional).")
    last_name = graphene.String(description="Last name of the user (optional).")

class UpdateProfileInput(graphene.InputObjectType):
    """
    Input type for updating user profile information.
    All fields are optional, as a user might only update a subset of their profile.
    """
    first_name = graphene.String(description="New first name for the user.")
    last_name = graphene.String(description="New last name for the user.")
    email = graphene.String(description="New email address for the user.")
    username = graphene.String(description="New username for the user.")

class AddressInput(graphene.InputObjectType):
    """
    Input type for adding or updating an address.
    """
    # id is not required for AddAddressMutation, but is for UpdateAddressMutation.
    # It's kept here as an optional field for flexibility.
    id = graphene.ID(description="Global ID of the address (required for updates).")
    street_address = graphene.String(required=True, description="Street address.")
    apartment_address = graphene.String(description="Apartment, suite, etc.")
    city = graphene.String(required=True, description="City of the address.")
    state_province = graphene.String(description="State or province of the address.")
    postal_code = graphene.String(required=True, description="Postal code of the address.")
    country = graphene.String(required=True, description="Country of the address.")
    address_type = graphene.String(default_value='shipping', description="Type of address (e.g., 'shipping', 'billing').")
    default = graphene.Boolean(description="Whether this address should be set as the default for its type.")

# --- Helper Function for User Role ---
def get_user_role(user):
    """Determines and returns the user's role."""
    if user.is_superuser:
        return "ADMIN"
    elif user.is_staff:
        return "STAFF"
    else:
        return "NORMAL"

# --- Mutations ---
class LoginUserMutation(graphene.Mutation):
    class Arguments:
        input = LoginUserInput(required=True)

    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserType)
    user_role = graphene.String(description="The role of the authenticated user (ADMIN, STAFF, or NORMAL).") # New field
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        try:
            user = authenticate(
                username=input.username_or_email,
                password=input.password
            )

            if user is None and '@' in input.username_or_email:
                try:
                    username = UserModel.objects.get(
                        email=input.username_or_email
                    ).username
                    user = authenticate(
                        username=username,
                        password=input.password
                    )
                except UserModel.DoesNotExist:
                    pass

            if user is None:
                return cls(
                    success=False,
                    errors=["Invalid credentials"],
                    token=None,
                    refresh_token=None,
                    user=None,
                    user_role=None # Return None for role on failure
                )

            if not user.is_active:
                return cls(
                    success=False,
                    errors=["Account is inactive"],
                    token=None,
                    refresh_token=None,
                    user=None,
                    user_role=None # Return None for role on failure
                )

            token = get_token(user)
            refresh_token = create_refresh_token(user)

            # Determine user role
            user_role = get_user_role(user)

            print(f"User '{user.username}' logged in. Role: {user_role}")
            print(f"Token: {token}")
            print(f"Refresh Token: {refresh_token}")

            return cls(
                success=True,
                token=token,
                refresh_token=refresh_token,
                user=user,
                user_role=user_role, # Include the user role
                errors=None
            )

        except Exception as e:
            return cls(
                success=False,
                errors=[f"Authentication failed: {str(e)}"],
                token=None,
                refresh_token=None,
                user=None,
                user_role=None # Return None for role on failure
            )

class JWTAuthMutation(jwt_mutations.ObtainJSONWebToken):
    """
    Extends the default ObtainJSONWebToken to include the user object and role in the response.
    """
    user = graphene.Field(UserType, description="The authenticated user object.")
    user_role = graphene.String(description="The role of the authenticated user (ADMIN, STAFF, or NORMAL).") # New field

    @classmethod
    def mutate(cls, root, info, **kwargs):
        result = super().mutate(root, info, **kwargs)
        if result.token and result.payload:
            try:
                user = UserModel.objects.get(pk=result.payload['user_id'])
                result.user = user
                result.user_role = get_user_role(user) # Set the user role
            except UserModel.DoesNotExist:
                result.user = None
                result.user_role = None
            except KeyError:
                result.user = None
                result.user_role = None
        return result

class RegisterUserMutation(graphene.Mutation):
    """
    Registers a new user and automatically logs them in.
    """
    class Arguments:
        input = RegisterUserInput(required=True, description="Input for new user registration.")

    user = graphene.Field(UserType, description="The newly registered user object.")
    token = graphene.String(description="The JWT access token for the new user.")
    refresh_token = graphene.String(description="The JWT refresh token for the new user.")
    user_role = graphene.String(description="The role of the newly registered user (NORMAL by default).") # New field
    success = graphene.Boolean(description="Indicates if the registration was successful.")
    errors = graphene.List(graphene.String, description="List of errors if the registration failed.")

    @classmethod
    def mutate(cls, root, info, input):
        # Check for existing username
        if UserModel.objects.filter(username=input.username).exists():
            return cls(
                user=None,
                token=None,
                refresh_token=None,
                user_role=None,
                success=False,
                errors=["Username already exists"]
            )
        # Check for existing email
        if UserModel.objects.filter(email=input.email).exists():
            return cls(
                user=None,
                token=None,
                refresh_token=None,
                user_role=None,
                success=False,
                errors=["Email already exists"]
            )
        try:
            # Create the user
            user = UserModel.objects.create_user(
                username=input.username,
                email=input.email,
                password=input.password
            )
            # Set optional fields
            if input.first_name:
                user.first_name = input.first_name
            if input.last_name:
                user.last_name = input.last_name
            user.save()

            # By default, a newly registered user is 'NORMAL'
            # If you have a specific flow for staff/admin registration, that would be separate.
            user_role = get_user_role(user) # Should be NORMAL for new registrations

            return cls(
                user=user,
                token=get_token(user),
                refresh_token=get_refresh_token(user),
                user_role=user_role, # Include the user role
                success=True,
                errors=None
            )
        except Exception as e:
            # Catch any unexpected errors during user creation
            return cls(
                user=None,
                token=None,
                refresh_token=None,
                user_role=None,
                success=False,
                errors=[f"An unexpected error occurred during registration: {str(e)}"]
            )

# --- Other Mutations (No changes needed, as they use login_required which relies on context) ---
class LogoutUserMutation(graphene.Mutation):
    success = graphene.Boolean(description="Indicates if the logout was successful.")
    errors = graphene.List(graphene.String, description="List of errors if logout failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info):
        return cls(success=True, errors=None)

class UpdateProfileMutation(graphene.Mutation):
    class Arguments:
        input = UpdateProfileInput(required=True, description="Input for updating user profile.")

    user = graphene.Field(UserType, description="The updated user object.")
    success = graphene.Boolean(description="Indicates if the profile update was successful.")
    errors = graphene.List(graphene.String, description="List of errors if the profile update failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
        user = info.context.user
        try:
            updated = False
            for field in ['first_name', 'last_name', 'email', 'username']:
                input_value = getattr(input, field, None)
                if input_value is not None and input_value != '':
                    if field in ['email', 'username']:
                        if UserModel.objects.filter(**{field: input_value}).exclude(pk=user.pk).exists():
                            return cls(
                                user=None,
                                success=False,
                                errors=[f"{field.capitalize()} '{input_value}' is already in use by another account."]
                            )
                    setattr(user, field, input_value)
                    updated = True

            if updated:
                user.save()
                return cls(user=user, success=True, errors=None)
            else:
                return cls(user=user, success=True, errors=["No fields provided for update."])

        except Exception as e:
            return cls(user=None, success=False, errors=[f"An unexpected error occurred during profile update: {str(e)}"])

class AddAddressMutation(graphene.Mutation):
    class Arguments:
        input = AddressInput(required=True, description="Input for adding a new address.")

    address = graphene.Field(AddressType, description="The newly created address object.")
    success = graphene.Boolean(description="Indicates if the address was added successfully.")
    errors = graphene.List(graphene.String, description="List of errors if adding address failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
        user = info.context.user
        try:
            if input.default:
                Address.objects.filter(
                    user=user,
                    address_type=input.address_type,
                    default=True
                ).update(default=False)

            address_data = {k: v for k, v in input.__dict__.items() if v is not None and k != 'id'}
            address_data['user'] = user

            address = Address.objects.create(**address_data)

            return cls(address=address, success=True, errors=None)
        except Exception as e:
            return cls(address=None, success=False, errors=[f"An unexpected error occurred while adding address: {str(e)}"])

class UpdateAddressMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="Global ID of the address to update.")
        input = AddressInput(required=True, description="Input containing updated address details.")

    address = graphene.Field(AddressType, description="The updated address object.")
    success = graphene.Boolean(description="Indicates if the address was updated successfully.")
    errors = graphene.List(graphene.String, description="List of errors if updating address failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info, id, input):
        try:
            _, address_pk = from_global_id(id)
            address = Address.objects.get(pk=address_pk, user=info.context.user)

            if input.default is not None and input.default:
                Address.objects.filter(
                    user=info.context.user,
                    address_type=input.address_type,
                    default=True
                ).exclude(pk=address_pk).update(default=False)

            updated = False
            for field in vars(input):
                if field == 'id':
                    continue
                input_value = getattr(input, field, None)
                if input_value is not None:
                    setattr(address, field, input_value)
                    updated = True

            if updated:
                address.save()
                return cls(address=address, success=True, errors=None)
            else:
                return cls(address=address, success=True, errors=["No fields provided for update."])

        except Address.DoesNotExist:
            return cls(address=None, success=False, errors=["Address not found or does not belong to the user."])
        except Exception as e:
            return cls(address=None, success=False, errors=[f"An unexpected error occurred while updating address: {str(e)}"])

class DeleteAddressMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="Global ID of the address to delete.")

    success = graphene.Boolean(description="Indicates if the address was deleted successfully.")
    errors = graphene.List(graphene.String, description="List of errors if deleting address failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        try:
            _, address_pk = from_global_id(id)
            address = Address.objects.get(pk=address_pk, user=info.context.user)

            address.delete()
            return cls(success=True, errors=None)
        except Address.DoesNotExist:
            return cls(success=False, errors=["Address not found or does not belong to the user."])
        except Exception as e:
            return cls(success=False, errors=[f"An unexpected error occurred while deleting address: {str(e)}"])

class UserProfileMutations(graphene.ObjectType):
    """
    Root mutation class for all user and address related operations.
    """
    # Authentication
    login = LoginUserMutation.Field(description="Logs in a user with username/email and password and returns their role.")
    token_auth = JWTAuthMutation.Field(description="Obtains a JWT token for a user (standard graphql_jwt) and returns their role.")
    verify_token = jwt_mutations.Verify.Field(description="Verifies the validity of a JWT token.")
    refresh_token = jwt_mutations.Refresh.Field(description="Refreshes an expired JWT token using a refresh token.")
    delete_token_cookie = graphql_jwt.DeleteJSONWebTokenCookie.Field(description="Deletes the JWT token cookie (for HTTP-only cookies).")
    delete_refresh_token_cookie = graphql_jwt.DeleteRefreshTokenCookie.Field(description="Deletes the JWT refresh token cookie (for HTTP-only cookies).")

    # User operations
    register = RegisterUserMutation.Field(description="Registers a new user account and returns their default role.")
    logout = LogoutUserMutation.Field(description="Logs out the current user (primarily client-side token removal).")
    update_profile = UpdateProfileMutation.Field(description="Updates the authenticated user's profile information.")

    # Address operations
    add_address = AddAddressMutation.Field(description="Adds a new address for the authenticated user.")
    update_address = UpdateAddressMutation.Field(description="Updates an existing address for the authenticated user.")
    delete_address = DeleteAddressMutation.Field(description="Deletes an address for the authenticated user.")