import graphene
from .types import OrderType, OrderItemType, TransactionType
from .models import Order, OrderItem, Transaction

class Query(graphene.ObjectType):
    orders = graphene.List(
        OrderType,
        offset=graphene.Int(description="The number of items to skip from the beginning."),
        limit=graphene.Int(description="The maximum number of items to return."),
        status=graphene.String(description="Filter orders by their status (e.g., 'pending', 'processing', 'completed')."),
        user_id=graphene.ID(description="Filter orders by a specific user's ID.")
    )
    order_items = graphene.List(OrderItemType)
    transactions = graphene.List(TransactionType)
    order_by_id = graphene.Field(OrderType, id=graphene.ID(required=True)) # Changed to ID for consistency
    order_count = graphene.Int(
        status=graphene.String(description="Count orders by a specific status."),
        user_id=graphene.ID(description="Count orders for a specific user's ID."),
        description="Returns the total count of orders, optionally filtered by status or user."
    )

    def resolve_orders(root, info, offset=None, limit=None, status=None, user_id=None):
        queryset = Order.objects.all()

        if status:
            queryset = queryset.filter(status=status)
        if user_id:
            queryset = queryset.filter(user_id=user_id) # Assuming 'user' is a ForeignKey to User model

        if offset is not None:
            queryset = queryset[offset:]
        if limit is not None:
            queryset = queryset[:limit]

        return queryset

    def resolve_order_items(root, info):
        return OrderItem.objects.all()

    def resolve_transactions(root, info):
        return Transaction.objects.all()

    def resolve_order_by_id(root, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

    def resolve_order_count(root, info, status=None, user_id=None):
        queryset = Order.objects.all()
        if status:
            queryset = queryset.filter(status=status)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset.count()