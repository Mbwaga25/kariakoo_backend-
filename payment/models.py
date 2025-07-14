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

from django.db import models
from django.utils.translation import gettext_lazy as _
from payment.models import PaymentGateway
from vendors.models import Vendor



class PaymentTransaction(models.Model):
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True,
        verbose_name=_("Vendor")
    )

    payed_to = models.CharField(
        max_length=20,
        verbose_name=_("Payed To")
    )

    gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("Payment Gateway")
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Transaction Reference")
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Transaction Amount")
    )

    status = models.CharField(max_length=20)

    response_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Gateway Response")
    )

    # Fields populated by callback
    result_type = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_("Result Type")
    )

    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Transaction ID")
    )

    gateway_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Gateway Amount")
    )

    gateway_hash = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Hash from Gateway")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    def __str__(self):
        return f"{self.reference} ({self.status})"
