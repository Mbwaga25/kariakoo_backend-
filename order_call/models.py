# order_call/models.py

from django.db import models
import uuid

class OrderCallRequest(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONTACTED = 'CONTACTED', 'Contacted'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    details = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request from {self.name} ({self.phone}) - {self.status}"
    
    class Meta:
        ordering = ['-created_at']


class OrderCallFile(models.Model):
    # Organizes uploads into folders by year/month/day
    def get_upload_path(instance, filename):
        return f'order_calls/{instance.request.created_at.strftime("%Y/%m/%d")}/{filename}'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        OrderCallRequest, 
        related_name='files', 
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for request {self.request.id}"