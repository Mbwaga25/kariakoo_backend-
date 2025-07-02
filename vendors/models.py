from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Vendor(models.Model):
    VENDOR_TYPES = [
        ('product', 'Product Vendor'),
        ('food', 'Food Vendor'),
        ('service', 'Service Provider'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES)
    company_name = models.CharField(max_length=100)
    tin_number = models.CharField(max_length=20, blank=True, null=True)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    is_approved = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.company_name} ({self.get_vendor_type_display()})"

class ProductVendor(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='product_vendor')
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} by {self.vendor.company_name}"

class ProductImage(models.Model):
    product = models.ForeignKey(ProductVendor, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/',
                            validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.product_name}"

class FoodVendor(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='food_vendor')
    cuisine_type = models.CharField(max_length=50)
    menu_description = models.TextField()
    has_vegetarian = models.BooleanField(default=False)
    has_vegan = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.cuisine_type} by {self.vendor.company_name}"

class ServiceProvider(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='service_provider')
    service_name = models.CharField(max_length=100)
    service_description = models.TextField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.service_name} by {self.vendor.company_name}"