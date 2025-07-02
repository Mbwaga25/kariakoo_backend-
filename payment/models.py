from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class PaymentGateway(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Gateway Name"))
    is_active = models.BooleanField(default=True)
    credentials = models.JSONField(null=True, blank=True, verbose_name=_("Credentials"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Payment Gateway")
        verbose_name_plural = _("Payment Gateways")


class TransactionStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")


class PaymentTransaction(models.Model):
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.PROTECT, related_name="transactions")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=100, unique=True, verbose_name=_("Transaction Reference"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Amount"))
    currency = models.CharField(max_length=10, default="TZS")
    status = models.CharField(
        max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    response_data = models.JSONField(null=True, blank=True, verbose_name=_("Gateway Response"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} ({self.status})"
