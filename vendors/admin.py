from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Vendor, ProductVendor, ProductImage, FoodVendor, ServiceProvider

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVendorAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

admin.site.register(Vendor)
admin.site.register(ProductVendor, ProductVendorAdmin)
admin.site.register(FoodVendor)
admin.site.register(ServiceProvider)