# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem, PromoCode, Transaction

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'client_name',          # Changed from 'guest_email' related name
        'client_phone',
        'client_email',         # Changed from 'guest_email'
        'order_date',
        'status',
        'total_amount',
        'discount_amount',
        'promo_code',
        'currency',
        'estimated_delivery_start',
    )
    list_filter = ('status', 'order_date', 'currency')
    search_fields = ('user__email', 'client_email', 'client_name', 'client_phone', 'id')
    raw_id_fields = ('user', 'billing_address', 'shipping_address', 'store', 'promo_code')
    readonly_fields = ('total_amount', 'discount_amount')  # Consider adding 'used_count' if you expose it here

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product',
        'product_variant',
        'quantity',
        'price_at_purchase',     # Changed from 'price'
        'final_price_per_unit',  # New field
        'total_price',           # New field
        'store'
    )
    list_filter = ('order__status', 'product__name', 'store')
    search_fields = ('order__id', 'product__name', 'product_variant__name')
    raw_id_fields = ('order', 'product', 'product_variant', 'store')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'transaction_id', 'amount', 'status', 'timestamp', 'payment_method')
    list_filter = ('status', 'timestamp', 'payment_method')
    search_fields = ('order__id', 'transaction_id', 'payment_method')
    raw_id_fields = ('order',)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'is_percentage', 'valid_from', 'valid_to', 'is_active', 'max_uses', 'used_count')
    list_filter = ('is_active', 'is_percentage', 'valid_from', 'valid_to')
    search_fields = ('code',)
    fieldsets = (
        (None, {
            'fields': ('code', 'discount_amount', 'is_percentage', 'valid_from', 'valid_to', 'is_active')
        }),
        ('Usage', {
            'fields': ('max_uses', 'used_count'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('used_count',)  # Fixed syntax error here