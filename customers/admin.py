from django.contrib import admin
from .models import CustomerProfile, Address

class AddressInline(admin.TabularInline):
    model = Address
    extra = 1
    readonly_fields = ['created_at', 'updated_at']
    fields = (
        'full_name', 'phone_number', 'region', 'district', 'ward', 'village',
        'street_address', 'house_number', 'landmark',
        'address_type', 'default', 'tin_number', 'business_name', 'delivery_notes',
    )

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number']
    search_fields = ['user__username', 'phone_number']
    # Uncomment if you want to manage addresses inline:
    # inlines = [AddressInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'full_name', 'phone_number', 'region', 'district', 'ward',
        'village', 'street_address', 'house_number', 'landmark',
        'address_type', 'default'
    ]
    list_filter = ['address_type', 'default', 'region']
    search_fields = ['user__username', 'full_name', 'phone_number', 'region', 'district', 'ward']
    readonly_fields = ['created_at', 'updated_at']
