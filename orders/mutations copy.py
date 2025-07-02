import graphene
from graphene import InputObjectType
from decimal import Decimal
from typing import Optional

from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model

from .models import Order, OrderItem, Transaction, PromoCode
from .types import OrderType, TransactionType
from customers.models import Address
from products.models import Product, ProductVariant
from stores.models import Store
from orders.helper.Id_helper import decode_global_id


class OrderItemInput(InputObjectType):
    productId = graphene.ID(required=True)
    productVariantId = graphene.ID(required=False)
    quantity = graphene.Int(required=True)
    storeId = graphene.ID(required=True)


class AddressInput(InputObjectType):
    street_address = graphene.String(required=True)
    apartment_address = graphene.String(required=False)
    city = graphene.String(required=True)
    postal_code = graphene.String(required=True)
    country = graphene.String(required=True)
    address_type = graphene.String(required=True)
    default = graphene.Boolean(default_value=False)


class FinalizeOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    transaction = graphene.Field(TransactionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        orderItems = graphene.List(OrderItemInput, required=True)
        clientEmail = graphene.String(required=False)
        userId = graphene.ID(required=False)
        storeId = graphene.ID(required=True)
        clientName = graphene.String(required=False)
        clientPhone = graphene.String(required=False)
        promoCode = graphene.String(required=False)
        client_address = graphene.String(required=False)
        customerComment = graphene.String(required=False)

    @classmethod
    @db_transaction.atomic
    def mutate(cls, root, info, orderItems, clientEmail=None, userId=None,
               storeId=None, clientName=None, clientPhone=None,
               promoCode=None, streetAddress=None, customerComment=None):
        
        User = get_user_model()
        user = None

        if userId:
            user_pk = decode_global_id(userId)
            user = User.objects.filter(pk=user_pk).first()
            if not user:
                raise Exception("User not found.")

        if not user and not clientEmail:
            raise Exception("Either user ID or client email must be provided.")

        store_pk = decode_global_id(storeId)
        store_instance = Store.objects.filter(pk=store_pk).first()
        if not store_instance:
            raise Exception("Store not found.")

        promo_code_instance = None
        if promoCode:
            promo_code_instance = PromoCode.objects.filter(code=promoCode).first()
            if not promo_code_instance or not promo_code_instance.is_valid():
                raise Exception("Invalid or expired promo code.")

        order = Order.objects.create(
            user=user,
            client_email=clientEmail,
            client_name=clientName,
            client_phone=clientPhone,
            status='pending',
            total_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            store=store_instance,
            currency='TZS',
            promo_code=promo_code_instance,
            street_address=streetAddress,
            customer_comment=customerComment
        )

        for item_input in orderItems:
            product = Product.objects.filter(pk=decode_global_id(item_input.productId)).first()
            if not product:
                raise Exception(f"Product with ID {item_input.productId} not found.")

            product_variant = None
            if item_input.productVariantId:
                product_variant = ProductVariant.objects.filter(pk=decode_global_id(item_input.productVariantId)).first()
                if not product_variant:
                    raise Exception(f"Product variant with ID {item_input.productVariantId} not found.")

            item_store = Store.objects.filter(pk=decode_global_id(item_input.storeId)).first()
            if not item_store:
                raise Exception(f"Store with ID {item_input.storeId} not found.")

            final_price = product.price

            OrderItem.objects.create(
                order=order,
                product=product,
                product_variant=product_variant,
                quantity=item_input.quantity,
                price_at_purchase=product.price,
                final_price_per_unit=final_price,
                total_price=final_price * item_input.quantity,
                store=item_store
            )

        order.refresh_from_db()
        if promo_code_instance:
            order.promo_code = promo_code_instance
            order.save()
        order.update_totals()

        if promo_code_instance:
            promo_code_instance.used_count += 1
            promo_code_instance.save()

        order.status = 'processing'
        order.save()

        return FinalizeOrder(
            order=order,
            transaction=None,
            success=True,
            message="Order created successfully"
        )


class OrderMutations(graphene.ObjectType):
    finalize_order = FinalizeOrder.Field()
