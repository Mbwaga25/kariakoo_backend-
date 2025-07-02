# customers/mutations.py
import graphene
from .models import Address
from .schema_types import AddressType
from graphql_jwt.decorators import login_required

class AddressInput(graphene.InputObjectType):
    id = graphene.ID()
    full_name = graphene.String(required=True)
    phone_number = graphene.String(required=True)
    region = graphene.String(required=True)
    district = graphene.String(required=True)
    ward = graphene.String(required=True)
    street_address = graphene.String(required=True)
    landmark = graphene.String()
    delivery_notes = graphene.String()
    tin_number = graphene.String()
    business_name = graphene.String()
    address_type = graphene.String(default_value='shipping')
    default = graphene.Boolean()

class CreateAddressMutation(graphene.Mutation):
    class Arguments:
        input = AddressInput(required=True)

    address = graphene.Field(AddressType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user if info.context.user.is_authenticated else None

        try:
            if input.default and user:
                # Unset other default addresses for this user of the same type
                Address.objects.filter(user=user, address_type=input.address_type, default=True).update(default=False)

            address = Address.objects.create(
                user=user,
                full_name=input.full_name,
                phone_number=input.phone_number,
                region=input.region,
                district=input.district,
                ward=input.ward,
                street_address=input.street_address,
                landmark=input.landmark,
                delivery_notes=input.delivery_notes,
                tin_number=input.tin_number,
                business_name=input.business_name,
                address_type=input.address_type,
                default=input.default if user else False
            )
            return cls(address=address, success=True)
        except Exception as e:
            return cls(address=None, success=False, errors=[str(e)])


class UpdateAddressMutation(graphene.Mutation):
    class Arguments:
        input = AddressInput(required=True)

    address = graphene.Field(AddressType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
        user = info.context.user
        if not input.id:
            return cls(address=None, success=False, errors=["Address ID is required for update."])

        try:
            address = Address.objects.get(pk=input.id, user=user)

            # Handle default address logic
            if input.default and not address.default: # If changing to default
                Address.objects.filter(user=user, address_type=input.address_type, default=True).exclude(pk=address.id).update(default=False)

            # Update fields if they are provided in input
            for field, value in input.items():
                if field == 'id': continue # Don't try to set id
                if value is not None: # Allows unsetting with null if model field allows
                     setattr(address, field, value)

            address.save()
            return cls(address=address, success=True)
        except Address.DoesNotExist:
            return cls(address=None, success=False, errors=["Address not found or access denied."])
        except Exception as e:
            return cls(address=None, success=False, errors=[str(e)])


class DeleteAddressMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        user = info.context.user
        try:
            address = Address.objects.get(pk=id, user=user)
            address.delete()
            return cls(success=True)
        except Address.DoesNotExist:
            return cls(success=False, errors=["Address not found or access denied."])
        except Exception as e:
            return cls(success=False, errors=[str(e)])


class CustomerMutations(graphene.ObjectType):
    create_address = CreateAddressMutation.Field()
    update_address = UpdateAddressMutation.Field()
    delete_address = DeleteAddressMutation.Field()