from django.db import models
from django.conf import settings

class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='addresses',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    # Common fields
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    delivery_notes = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.CharField(max_length=255)
    house_number = models.CharField(max_length=50, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
  

    # Billing-only fields
    tin_number = models.CharField(max_length=20, blank=True, null=True)
    business_name = models.CharField(max_length=255, blank=True, null=True)

    # Address type
    address_type_choices = [
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
    ]
    address_type = models.CharField(max_length=10, choices=address_type_choices, default='shipping')
    default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        identity = self.user.username if self.user else self.full_name
        return f"{identity} - {self.street_address}, {self.ward}, {self.district}, {self.region} ({self.get_address_type_display()})"

    class Meta:
        verbose_name_plural = "Addresses"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'address_type'],
                condition=models.Q(default=True),
                name='unique_default_address_per_type'
            )
        ]

class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username
