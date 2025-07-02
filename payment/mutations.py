import graphene
from django.contrib.auth import get_user_model
from graphql import GraphQLError

from .models import PaymentGateway, PaymentTransaction, TransactionStatus


from .types import PaymentTransactionType, TransactionStatusEnum

User = get_user_model()


class CreatePaymentTransaction(graphene.Mutation):
    """Creates a new payment transaction."""
    
    # Outputs: what the mutation will return
    transaction = graphene.Field(PaymentTransactionType)

    class Arguments:
        # Inputs: the data needed to create a transaction
        gateway_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)
        reference = graphene.String(required=True)
        amount = graphene.Decimal(required=True)
        currency = graphene.String(required=False, default_value="TZS")

    def mutate(self, info, gateway_id, user_id, reference, amount, currency="TZS"):
        try:
            gateway = PaymentGateway.objects.get(pk=gateway_id, is_active=True)
            user = User.objects.get(pk=user_id)

            transaction = PaymentTransaction.objects.create(
                gateway=gateway,
                user=user,
                reference=reference,
                amount=amount,
                currency=currency,
                status=TransactionStatus.PENDING # Always starts as pending
            )
            return CreatePaymentTransaction(transaction=transaction)

        except PaymentGateway.DoesNotExist:
            raise GraphQLError("Invalid or inactive payment gateway.")
        except User.DoesNotExist:
            raise GraphQLError("User not found.")
        except Exception as e:
            # Handle other potential errors, like a non-unique reference
            raise GraphQLError(f"An error occurred: {e}")


class UpdateTransactionStatus(graphene.Mutation):
    """Updates the status of an existing payment transaction."""
    
    # Outputs
    transaction = graphene.Field(PaymentTransactionType)

    class Arguments:
        # Inputs
        transaction_id = graphene.ID(required=True)
        status = graphene.Argument(TransactionStatusEnum, required=True)
        response_data = graphene.JSONString(required=False)

    def mutate(self, info, transaction_id, status, response_data=None):
        try:
            transaction = PaymentTransaction.objects.get(pk=transaction_id)
            
            # Update the fields
            transaction.status = status
            if response_data:
                transaction.response_data = response_data
            
            transaction.save()
            
            return UpdateTransactionStatus(transaction=transaction)
            
        except PaymentTransaction.DoesNotExist:
            raise GraphQLError("Transaction not found.")
        except Exception as e:
            raise GraphQLError(f"An error occurred: {e}")


class PaymentMutation(graphene.ObjectType):
    """Root mutation for the application."""
    create_payment_transaction = CreatePaymentTransaction.Field()
    update_transaction_status = UpdateTransactionStatus.Field()