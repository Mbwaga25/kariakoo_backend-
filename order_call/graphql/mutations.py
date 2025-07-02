import graphene
from graphene_file_upload.scalars import Upload
from .types import OrderCallRequestType
from ..models import OrderCallRequest, OrderCallFile
from graphql import GraphQLError
from uuid import UUID

class CreateOrderCallRequest(graphene.Mutation):
    success = graphene.Boolean()
    order_call_request = graphene.Field(OrderCallRequestType)

    class Arguments:
        name = graphene.String(required=True)
        phone = graphene.String(required=True)
        details = graphene.String(required=True)
        files = graphene.List(Upload, required=False)

    def mutate(self, info, name, phone, details, files=None):
        # Create the main request object with default status
        request_instance = OrderCallRequest.objects.create(
            name=name,
            phone=phone,
            details=details,
            status=OrderCallRequest.StatusChoices.PENDING.value  # Explicitly set as string value
        )

        # Handle file uploads if present
        if files:
            for file in files:
                OrderCallFile.objects.create(
                    request=request_instance,
                    file=file
                )
        
        return CreateOrderCallRequest(
            success=True, 
            order_call_request=request_instance
        )

class UpdateOrderCallStatus(graphene.Mutation):
    success = graphene.Boolean()
    order_call_request = graphene.Field(OrderCallRequestType)

    class Arguments:
        id = graphene.UUID(required=True)
        status = graphene.String(required=True)

    def mutate(self, info, id, status):
        # Security check
        user = info.context.user
        if not user.is_authenticated or not user.is_staff:
            raise GraphQLError("Permission denied: Staff members only.")

        # Validate status input
        valid_statuses = [choice.value for choice in OrderCallRequest.StatusChoices]
        if status not in valid_statuses:
            raise GraphQLError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        try:
            # Convert string UUID to UUID object for lookup
            request_instance = OrderCallRequest.objects.get(pk=UUID(str(id)))
            request_instance.status = status
            request_instance.save(update_fields=['status'])
            return UpdateOrderCallStatus(
                success=True, 
                order_call_request=request_instance
            )
        except OrderCallRequest.DoesNotExist:
            raise GraphQLError("Order call request not found.")
        except ValueError as e:
            raise GraphQLError(f"Invalid ID format: {str(e)}")

class DeleteOrderCallRequest(graphene.Mutation):
    success = graphene.Boolean()
    deleted_id = graphene.UUID()

    class Arguments:
        id = graphene.UUID(required=True)

    def mutate(self, info, id):
        # Security check
        user = info.context.user
        if not user.is_authenticated or not user.is_staff:
            raise GraphQLError("Permission denied: Staff members only.")

        try:
            # Convert string UUID to UUID object for lookup
            request_instance = OrderCallRequest.objects.get(pk=UUID(str(id)))
            deleted_id = request_instance.id
            request_instance.delete()
            return DeleteOrderCallRequest(
                success=True,
                deleted_id=deleted_id
            )
        except OrderCallRequest.DoesNotExist:
            raise GraphQLError("Order call request not found.")
        except ValueError as e:
            raise GraphQLError(f"Invalid ID format: {str(e)}")

class Mutation(graphene.ObjectType):
    create_order_call_request = CreateOrderCallRequest.Field()
    update_order_call_status = UpdateOrderCallStatus.Field()
    delete_order_call_request = DeleteOrderCallRequest.Field()