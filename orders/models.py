from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from products.models import Product, ProductVariant
from stores.models import Store
from customers.models import Address
from django.core.validators import MinValueValidator
from decimal import *


class PromoCode(models.Model):
    """
    Represents a promotional code that can be applied to an order.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Promo Code')
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Discount Amount')
    )
    is_percentage = models.BooleanField(
        default=False,
        verbose_name=_('Is Percentage Discount')
    )
    valid_from = models.DateTimeField(
        verbose_name=_('Valid From')
    )
    valid_to = models.DateTimeField(
        verbose_name=_('Valid To')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    max_uses = models.PositiveIntegerField(
        default=0,  # 0 means unlimited uses
        verbose_name=_('Maximum Uses')
    )
    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Used Count')
    )

    def __str__(self):
        return self.code

    def is_valid(self):
        """Check if promo code is currently valid"""
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and
                (self.max_uses == 0 or self.used_count < self.max_uses))

    class Meta:
        verbose_name = _('Promo Code')
        verbose_name_plural = _('Promo Codes')
        ordering = ['-valid_from']


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('User')
    )
    client_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Client Name')
    )
    client_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Client Adress')
    )
    client_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Client Phone')
    )
    client_email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_('Client Email')
    )

    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billing_orders',
        verbose_name=_('Billing Address')
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipping_orders',
        verbose_name=_('Shipping Address')
    )
    order_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Order Date')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('Store')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Total Amount')
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Total Discount Applied')
    )
    estimated_delivery_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Estimated Delivery Start')
    )
    estimated_delivery_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Estimated Delivery End')
    )
    currency = models.CharField(
        max_length=3,
        default='TZS',
        verbose_name=_('Currency')
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('Applied Promo Code')
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Internal Notes')
    )
    customer_comment = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Customer Comment')
    )

    def __str__(self):
        return f"Order #{self.id} - {self.order_date.strftime('%Y-%m-%d')} - {self.get_status_display()}"

    def calculate_total(self):
        """Calculate the order total based on items and discounts"""
        items_total = sum(item.total_price for item in self.items.all())
        return max(items_total - self.discount_amount, Decimal('0.00'))

    def update_totals(self):
        """Update order totals based on current items and discounts"""
        self.total_amount = self.calculate_total()
        self.save(update_fields=['total_amount'])

    def save(self, *args, **kwargs):
        # Populate client info from shipping address if not provided
        if not self.user and self.shipping_address:
            if not self.client_name:
                self.client_name = self.shipping_address.full_name
            if not self.client_phone:
                self.client_phone = self.shipping_address.phone_number

        # Apply promo code discount if exists
        if self.promo_code and self.promo_code.is_valid():
            if self.promo_code.is_percentage:
                self.discount_amount = (self.calculate_subtotal() * 
                                      self.promo_code.discount_amount / 100)
            else:
                self.discount_amount = self.promo_code.discount_amount

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order_date']),
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Order')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Product')
    )
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('Product Variant')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity')
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Price at Purchase')
    )
    final_price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Final Price Per Unit')
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Total Price for Item')
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Store')
    )

    def __str__(self):
        variant_info = f" ({self.product_variant})" if self.product_variant else ""
        return f"{self.quantity} x {self.product.name}{variant_info}"

    def save(self, *args, **kwargs):
        if not self.price_at_purchase:
            self.price_at_purchase = self.product.price
        if not self.final_price_per_unit:
            self.final_price_per_unit = self.price_at_purchase
        self.total_price = self.quantity * self.final_price_per_unit
        super().save(*args, **kwargs)
        self.order.update_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_totals()

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product', 'product_variant'],
                name='unique_product_variant_per_order',
                condition=models.Q(product_variant__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_product_per_order',
                condition=models.Q(product_variant__isnull=True)
            )
        ]


class Transaction(models.Model):
    PAYMENT_METHODS = [
        ('card', _('Credit/Debit Card')),
        ('mobile', _('Mobile Payment')),
        ('cash', _('Cash on Delivery')),
        ('bank', _('Bank Transfer')),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('Order')
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Transaction ID')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Amount')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Transaction Time')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        verbose_name=_('Payment Method')
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', _('Success')),
            ('pending', _('Pending')),
            ('failed', _('Failed')),
            ('refunded', _('Refunded')),
        ],
        default='pending',
        verbose_name=_('Transaction Status')
    )
    response_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Gateway Response')
    )

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status} - {self.amount}"

    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-timestamp']