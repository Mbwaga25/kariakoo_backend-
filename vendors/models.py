
from django.db import models
from django.core.validators import FileExtensionValidator

from django.db import models
from django.core.validators import FileExtensionValidator

class Vendor(models.Model):
    VENDOR_TYPES = [
        ('product', 'Product Vendor'),
        ('service', 'Service Provider'),
        ('sponsor', 'Sponsor/Institution Vendor'),
    ]

    fullname = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES)
    company_name = models.CharField(max_length=100)
    tin_number = models.CharField(max_length=20, blank=True, null=True)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    # ✅ New fields for business type and category
    business_category = models.CharField(max_length=100, blank=True, null=True)
    retail_wholesale = models.JSONField(blank=True, null=True)  # ["Retail", "Wholesale"]

    is_approved = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.company_name} ({self.get_vendor_type_display()})"

class ProductVendor(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='product_vendor')
    status = models.CharField(max_length=50, default='PENDING')
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} by {self.vendor.company_name}"

class ProductImage(models.Model):
    product = models.ForeignKey(ProductVendor, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='product_images/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.product_name}"

class FoodVendor(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='food_vendor')
    cuisine_type = models.CharField(max_length=50, blank=True, null=True)
    menu_description = models.TextField(blank=True, null=True)
    has_vegetarian = models.BooleanField(default=False)
    has_vegan = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.cuisine_type or 'Food'} by {self.vendor.company_name}"

class ServiceProvider(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='service_provider')
    service_name = models.CharField(max_length=100)
    service_description = models.TextField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    boothSize = models.TextField(blank=True, null=True)
    powerNeeded =models.BooleanField(default=False)
    menu_description = models.TextField(blank=True, null=True)
    package= models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.service_name} by {self.vendor.company_name}"

class SponsorInstitutionVendor(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='sponsor_vendor')
    status = models.CharField(max_length=50, default='ON_PROCESSING')
    institution_name = models.CharField(max_length=100)
    package = models.CharField(max_length=100, blank=True, null=True)
    partnershipInterest = models.CharField(max_length=100, blank=True, null=True)
    orgRep = models.CharField(max_length=100, blank=True, null=True)
    partnershipInterest = models.CharField(max_length=100, blank=True, null=True) 
    
    # ✅ ImageField instead of CharField
    companyLogo = models.ImageField(
        upload_to='sponsor_logos/',  # Folder inside MEDIA_ROOT
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.institution_name} sponsor for {self.vendor.company_name}"
