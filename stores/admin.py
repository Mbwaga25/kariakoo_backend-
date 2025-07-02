from django.contrib import admin
from .models import Store, StoreProduct
from products.models import ProductVariant  # Adjust path if needed

# Unregister Store if it was registered elsewhere
from django.contrib.admin.sites import AlreadyRegistered
try:
    admin.site.unregister(Store)  # Prevent duplicate registration
except AlreadyRegistered:
    pass

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'store_type', 'is_active', 'city', 'country', 'created_at')
    list_filter = ('is_active', 'store_type', 'country')
    search_fields = ('name', 'slug', 'email', 'phone_number', 'owner__email')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    # prepopulated_fields = {"slug": ("name",)}
    ordering = ['-created_at']
    readonly_fields = ('created_at', 'updated_at', 'slug')