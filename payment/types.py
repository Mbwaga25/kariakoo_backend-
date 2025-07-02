import graphene
from graphene_django.types import DjangoObjectType

# Import your models
from orders.models import Transaction
from payment.models import PaymentTransaction, PaymentGateway

# Define Enums at the top level for better reusability
class TransactionStatusEnum(graphene.Enum):
    """An enumeration for transaction statuses."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

# First GraphQL type for the Transaction model
class OrderTransactionType(DjangoObjectType):
    """A GraphQL type for the Order Transaction model."""
    class Meta:
        model = Transaction
        fields = "__all__"

class PaymentGatewayType(DjangoObjectType):
    """A GraphQL type for the Order Transaction model."""
    class Meta:
        model = PaymentGateway
        fields = "__all__"

# Second, uniquely named GraphQL type for the PaymentTransaction model
class PaymentTransactionType(DjangoObjectType):
    """A GraphQL type for the Payment Transaction model."""
    class Meta:
        model = PaymentTransaction
        fields = "__all__"