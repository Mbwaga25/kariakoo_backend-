# order_call/admin.py

from django.contrib import admin
from .models import OrderCallRequest, OrderCallFile

class OrderCallFileInline(admin.TabularInline):
    """Allows you to see and add files directly from the request page in admin."""
    model = OrderCallFile
    extra = 1  # How many extra empty file slots to show
    readonly_fields = ('uploaded_at',)

@admin.register(OrderCallRequest)
class OrderCallRequestAdmin(admin.ModelAdmin):
    # These inlines will appear on the OrderCallRequest change page
    inlines = [OrderCallFileInline]
    
    list_display = ('name', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'details')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'phone', 'details', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',) # Make this section collapsible
        }),
    )