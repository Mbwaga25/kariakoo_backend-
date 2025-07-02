from django.contrib import admin
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from products.models import Product
from django.core.validators import MinValueValidator  # ✅ Required
from products.models import ProductVariant  # Ensure this path is correct

# --- Store Model ---
class Store(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    # Contact Info
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)

    # Address Info
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True, verbose_name="State/Province")
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Geolocation
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='owned_stores',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    opening_hours = models.JSONField(blank=True, null=True)

    store_type = models.CharField(
        max_length=10,
        choices=[
            ('retail', 'Retail'),
            ('wholesale', 'Wholesale'),
            ('both', 'Retail & Wholesale')
        ],
        default='retail'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


# --- StoreProduct Model ---
class StoreProduct(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='store_products'
    )
    product = models.ForeignKey(Product, related_name='store_listings', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='store_products'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Alert when stock reaches this level"
    )
    is_available = models.BooleanField(default=True)
    wholesale_minimum_quantity = models.PositiveIntegerField(null=True, blank=True)
    sku_in_store = models.CharField(max_length=100, blank=True, null=True)
    location_in_store = models.CharField(max_length=100, blank=True, null=True)

    last_stock_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('store', 'product')
        verbose_name = "Store Product"
        verbose_name_plural = "Store Products"
        ordering = ['-last_stock_update']
        constraints = [
            models.UniqueConstraint(fields=['store', 'product'], name='unique_product_per_store')
        ]
        indexes = [
            models.Index(fields=['store', 'product']),
            models.Index(fields=['is_available', 'stock']),
        ]

    def __str__(self):
        return f"{self.product.name} at {self.store.name} (Stock: {self.stock}, Price: {self.price})"
    



# --- Admin Registration ---
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'store_type', 'is_active', 'city', 'country', 'created_at')
    list_filter = ('is_active', 'store_type', 'country')
    search_fields = ('name', 'slug', 'email', 'phone_number', 'owner__email')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    prepopulated_fields = {"slug": ("name",)}
    ordering = ['-created_at']


@admin.register(StoreProduct)
class StoreProductAdmin(admin.ModelAdmin):
    list_display = ('store', 'product', 'product_variant', 'price', 'stock', 'is_available', 'last_stock_update')
    list_filter = ('is_available', 'store', 'product')
    search_fields = ('product__name', 'store__name', 'sku_in_store')
    autocomplete_fields = ('store', 'product', 'product_variant')
    readonly_fields = ('last_stock_update',)
    ordering = ['-last_stock_update']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    search_fields = ['sku', 'name']
    ordering = ['name']
