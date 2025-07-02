# orders/types.py
import graphene
from graphene_django import DjangoObjectType
from .models import Order, OrderItem, Transaction
from products.types import ProductType  
from customers.schema_types import AddressType 
from stores.types import StoreType


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        # fields = (
        #     'id', 'user', 'guest_email', 'billing_address', 'shipping_address',
        #     'order_date', 'status', 'total_amount', 'notes', 'store', 'items'
        # )
        fields = "__all__"


class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        # fields = ("id", "order", "product", "product_variant", "quantity", "price", "store")
        fields = "__all__"


class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction
        fields = ("id", "order", "transaction_id", "amount", "timestamp", "payment_method", "status", "response_data")




