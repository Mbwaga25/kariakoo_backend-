# schema.py (or queries.py)

import graphene
from graphene_django import DjangoObjectType
from .models import PaymentTransaction, PaymentGateway
from .types import (
    PaymentTransactionType, 
    TransactionStatusEnum,PaymentGatewayType
    
)

# --- Root Query Class ---
# This class defines the entry points for all read operations in your API.

class PaymentQuery(graphene.ObjectType):
    """
    Defines the root queries for the payment API.
    """
    # Query to get a single transaction by its ID
    transaction_by_id = graphene.Field(
        PaymentTransactionType, 
        id=graphene.ID(required=True, description="The ID of the transaction.")
    )

    # Query to get a list of all transactions, with optional filtering
    all_transactions = graphene.List(
        PaymentTransactionType,
        status=graphene.Argument(TransactionStatusEnum, required=False, description="Filter transactions by status."),
        user_id=graphene.ID(required=False, description="Filter transactions by user ID.")
    )

    # Query to get a single payment gateway by its ID
    gateway_by_id = graphene.Field(
        PaymentGatewayType,
        id=graphene.ID(required=True, description="The ID of the payment gateway.")
    )

    # Query to get a list of all available payment gateways
    all_gateways = graphene.List(
        PaymentGatewayType,
        is_active=graphene.Boolean(required=False, description="Filter gateways by active status.")
    )

    # --- Resolvers ---
    # These functions contain the logic to fetch the data for each query.

    def resolve_transaction_by_id(self, info, id):
        """
        Retrieves a single PaymentTransaction by its primary key.
        """
        try:
            return PaymentTransaction.objects.get(pk=id)
        except PaymentTransaction.DoesNotExist:
            return None

    def resolve_all_transactions(self, info, status=None, user_id=None):
        """
        Retrieves a list of PaymentTransactions, allowing filtering by status and/or user.
        """
        queryset = PaymentTransaction.objects.select_related("user", "gateway").all()
        
        if status:
            queryset = queryset.filter(status=status)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset

    def resolve_gateway_by_id(self, info, id):
        """
        Retrieves a single PaymentGateway by its primary key.
        """
        try:
            return PaymentGateway.objects.get(pk=id)
        except PaymentGateway.DoesNotExist:
            return None

    def resolve_all_gateways(self, info, is_active=None):
        """
        Retrieves a list of PaymentGateways, with an option to filter by active status.
        """
        queryset = PaymentGateway.objects.all()
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        return queryset

