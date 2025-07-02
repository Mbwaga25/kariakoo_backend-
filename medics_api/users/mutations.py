# users/mutations.py
import graphene
from django.contrib.auth import get_user_model
from customers.models import Address
from .schema_types import UserType, AddressType
from graphql_jwt.decorators import login_required
from graphql_jwt.shortcuts import get_token, get_refresh_token
from graphql_jwt import mutations as jwt_mutations
import graphql_jwt
from graphql_relay import from_global_id
from django.contrib.auth import authenticate
from graphql_jwt.shortcuts import create_refresh_token

UserModel = get_user_model()

# --- Input Types ---
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

# --- Mutations ---
class LoginUserMutation(graphene.Mutation):
    class Arguments:
        input = LoginUserInput(required=True)

    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserType)
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
                    user=None
                )

            if not user.is_active:
                return cls(
                    success=False,
                    errors=["Account is inactive"],
                    token=None,
                    refresh_token=None,
                    user=None
                )

            token = get_token(user)
            # refresh_token = get_refresh_token(user)
            refresh_token = create_refresh_token(user)

            print(f"Token: {token}")
            print(f"Refresh Token: {refresh_token}")

            return cls(
                success=True,
                token=token,
                refresh_token=refresh_token,
                user=user,
                errors=None
            )

        except Exception as e:
            return cls(
                success=False,
                errors=[f"Authentication failed: {str(e)}"],
                token=None,
                refresh_token=None,
                user=None
            )

class JWTAuthMutation(jwt_mutations.ObtainJSONWebToken):
    """
    Extends the default ObtainJSONWebToken to include the user object in the response.
    """
    user = graphene.Field(UserType, description="The authenticated user object.")

    @classmethod
    def mutate(cls, root, info, **kwargs):
        result = super().mutate(root, info, **kwargs)
        if result.token and result.payload: # Check for token existence before accessing payload
            try:
                user = UserModel.objects.get(pk=result.payload['user_id'])
                result.user = user
            except UserModel.DoesNotExist:
                result.user = None
            except KeyError:
                # Handle cases where 'user_id' might not be in the payload
                result.user = None
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
                success=False,
                errors=["Username already exists"]
            )
        # Check for existing email
        if UserModel.objects.filter(email=input.email).exists():
            return cls(
                user=None,
                token=None,
                refresh_token=None,
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

            return cls(
                user=user,
                token=get_token(user),
                refresh_token=get_refresh_token(user),
                success=True,
                errors=None
            )
        except Exception as e:
            # Catch any unexpected errors during user creation
            return cls(
                user=None,
                token=None,
                refresh_token=None,
                success=False,
                errors=[f"An unexpected error occurred during registration: {str(e)}"]
            )

class LogoutUserMutation(graphene.Mutation):
    """
    Logs out the current user. Note: For JWT, this primarily invalidates the client-side tokens.
    """
    success = graphene.Boolean(description="Indicates if the logout was successful.")
    errors = graphene.List(graphene.String, description="List of errors if logout failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info):
        # With JWT, "logout" typically means discarding the tokens on the client side.
        # The tokens themselves are not invalidated server-side unless blacklisted.
        # graphql_jwt provides `DeleteJSONWebTokenCookie` and `DeleteRefreshTokenCookie`
        # for HTTP-only cookie based token management, which are generally preferred for security.
        # This mutation primarily confirms the user was logged in to allow the operation.
        return cls(success=True, errors=None)

class UpdateProfileMutation(graphene.Mutation):
    """
    Updates the profile information of the authenticated user.
    """
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
                # Check if the input field is provided (not None or empty string for String fields)
                input_value = getattr(input, field, None)
                if input_value is not None and input_value != '': # Added check for empty string
                    # Handle unique fields (email, username) separately
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
                return cls(user=user, success=True, errors=["No fields provided for update."]) # Inform if no changes were made

        except Exception as e:
            return cls(user=None, success=False, errors=[f"An unexpected error occurred during profile update: {str(e)}"])

class AddAddressMutation(graphene.Mutation):
    """
    Adds a new address for the authenticated user.
    """
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
            # If the new address is set as default, unset previous default for the same type
            if input.default:
                Address.objects.filter(
                    user=user,
                    address_type=input.address_type,
                    default=True
                ).update(default=False)

            # Create the address instance
            # Use a dictionary comprehension to filter out None values and include 'user'
            address_data = {k: v for k, v in input.__dict__.items() if v is not None and k != 'id'}
            address_data['user'] = user

            address = Address.objects.create(**address_data)

            return cls(address=address, success=True, errors=None)
        except Exception as e:
            return cls(address=None, success=False, errors=[f"An unexpected error occurred while adding address: {str(e)}"])

class UpdateAddressMutation(graphene.Mutation):
    """
    Updates an existing address for the authenticated user.
    """
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
            # Decode the global ID to get the internal Django ID
            _, address_pk = from_global_id(id)
            address = Address.objects.get(pk=address_pk, user=info.context.user)

            # If the updated address is set as default, unset previous default for the same type
            if input.default is not None and input.default: # Check explicitly for True
                Address.objects.filter(
                    user=info.context.user,
                    address_type=input.address_type, # Ensure address_type is considered for default
                    default=True
                ).exclude(pk=address_pk).update(default=False) # Exclude the current address being updated

            # Update address fields
            updated = False
            for field in vars(input):
                if field == 'id': # Skip updating the ID field
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
    """
    Deletes an existing address for the authenticated user.
    """
    class Arguments:
        id = graphene.ID(required=True, description="Global ID of the address to delete.")

    success = graphene.Boolean(description="Indicates if the address was deleted successfully.")
    errors = graphene.List(graphene.String, description="List of errors if deleting address failed.")

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        try:
            # Decode the global ID
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
    login = LoginUserMutation.Field(description="Logs in a user with username/email and password.")
    token_auth = JWTAuthMutation.Field(description="Obtains a JWT token for a user (standard graphql_jwt).")
    verify_token = jwt_mutations.Verify.Field(description="Verifies the validity of a JWT token.")
    refresh_token = jwt_mutations.Refresh.Field(description="Refreshes an expired JWT token using a refresh token.")
    delete_token_cookie = graphql_jwt.DeleteJSONWebTokenCookie.Field(description="Deletes the JWT token cookie (for HTTP-only cookies).")
    delete_refresh_token_cookie = graphql_jwt.DeleteRefreshTokenCookie.Field(description="Deletes the JWT refresh token cookie (for HTTP-only cookies).")

    # User operations
    register = RegisterUserMutation.Field(description="Registers a new user account.")
    logout = LogoutUserMutation.Field(description="Logs out the current user (primarily client-side token removal).")
    update_profile = UpdateProfileMutation.Field(description="Updates the authenticated user's profile information.")

    # Address operations
    add_address = AddAddressMutation.Field(description="Adds a new address for the authenticated user.")
    update_address = UpdateAddressMutation.Field(description="Updates an existing address for the authenticated user.")
    delete_address = DeleteAddressMutation.Field(description="Deletes an address for the authenticated user.")