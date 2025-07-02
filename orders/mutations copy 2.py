import graphene
from graphene import InputObjectType
from decimal import Decimal
import re  # For phone number validation
from django.core.exceptions import ValidationError

from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model

from .models import Order, OrderItem, PromoCode
from .types import OrderType
from products.models import Product, ProductVariant
from stores.models import Store
from orders.helper.Id_helper import decode_global_id



def validate_tanzania_phone_number(phone):
    """
    Validate Tanzania phone number format:
    - Either starts with +255 followed by 9 digits (total 12 digits)
    - Or starts with 0 followed by 9 digits (total 10 digits)
    """
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'(?!^\+)[^\d]', '', phone)
    
    # Check for +255 format (12 digits total)
    if cleaned.startswith('+255'):
        if len(cleaned) != 12 or not cleaned[4:].isdigit():
            raise ValidationError(
                "Invalid international format. Use +255 followed by 9 digits (e.g. +255123456789)"
            )
    # Check for 0 format (10 digits total)
    elif cleaned.startswith('0'):
        if len(cleaned) != 10 or not cleaned[1:].isdigit():
            raise ValidationError(
                "Invalid local format. Use 0 followed by 9 digits (e.g. 0712345678)"
            )
    else:
        raise ValidationError(
            "Phone number must start with +255 (international) or 0 (local)"
        )
class OrderItemInput(InputObjectType):
    product_id = graphene.ID(required=True)
    product_variant_id = graphene.ID(required=False)
    quantity = graphene.Int(required=True)
    store_id = graphene.ID(required=True)


class FinalizeOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        order_items = graphene.List(OrderItemInput, required=True)
        client_email = graphene.String(required=False)
        user_id = graphene.ID(required=False)
        store_id = graphene.ID(required=True)
        client_name = graphene.String(required=False)
        client_phone = graphene.String(required=False)
        promo_code = graphene.String(required=False)
        client_address = graphene.String(required=False)
        customer_comment = graphene.String(required=False)

    @classmethod
    @db_transaction.atomic
    def mutate(cls, root, info, order_items, store_id, 
               client_email=None, user_id=None, client_name=None,
               client_phone=None, promo_code=None, client_address=None,
               customer_comment=None):
        User = get_user_model()
        user = None

        if user_id:
            user = User.objects.filter(pk=decode_global_id(user_id)).first()
            if not user:
                raise Exception("User not found.")

        # Phone number validation when user is not available
        if not user:
            if not client_phone:
                raise Exception("Phone number is required when user is not available")
            
            try:
                validate_tanzania_phone_number(client_phone)
            except ValidationError as e:
                raise Exception(str(e))

        store_instance = Store.objects.filter(pk=decode_global_id(store_id)).first()
        if not store_instance:
            raise Exception("Store not found.")

        promo_code_instance = None
        if promo_code:
            promo_code_instance = PromoCode.objects.filter(code=promo_code).first()
            if not promo_code_instance or not promo_code_instance.is_valid():
                raise Exception("Invalid or expired promo code.")

        order = Order.objects.create(
            user=user,
            client_email=client_email,
            client_name=client_name,
            client_phone=client_phone,
            status='pending',
            total_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            store=store_instance,
            currency='TZS',
            promo_code=promo_code_instance,
            client_address=client_address,
            customer_comment=customer_comment
        )

        for item_input in order_items:
            product = Product.objects.filter(pk=decode_global_id(item_input.product_id)).first()
            if not product:
                raise Exception(f"Product with ID {item_input.product_id} not found.")

            product_variant = None
            if item_input.product_variant_id:
                product_variant = ProductVariant.objects.filter(
                    pk=decode_global_id(item_input.product_variant_id)
                ).first()
                if not product_variant:
                    raise Exception(f"Product variant with ID {item_input.product_variant_id} not found.")

            item_store = Store.objects.filter(pk=decode_global_id(item_input.store_id)).first()
            if not item_store:
                raise Exception(f"Store with ID {item_input.store_id} not found.")

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
            success=True,
            message="Order created successfully"
        )


class OrderMutations(graphene.ObjectType):
    finalize_order = FinalizeOrder.Field()