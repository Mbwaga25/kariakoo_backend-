from django.contrib import admin, messages
from django import forms
from django.urls import path
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.db import transaction
from .models import (
    Brand, ProductCategory, Attribute, Tag,
    Product, ProductImage, ProductAttributeValue,
    ProductTagMap, ProductVariant, ProductSegment
)
import csv
import json
from io import StringIO, TextIOWrapper

# --- Inline Admin for Related Models ---

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 

class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1

class ProductTagMapInline(admin.TabularInline):
    model = ProductTagMap
    verbose_name = "Tag"
    verbose_name_plural = "Tags"
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    
# --- Product Import Form ---

class ProductImportForm(forms.Form):
    file_type = forms.ChoiceField(
        choices=[('csv', 'CSV'), ('json', 'JSON')],
        label="File Type"
    )
    import_file = forms.FileField(
        label="File to import",
        help_text="Upload a CSV or JSON file with product data"
    )
    update_existing = forms.BooleanField(
        required=False,
        label="Update existing products",
        help_text="Check to update existing products instead of skipping them"
    )

# --- Product Admin Configuration ---

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'is_globally_active', 'created_at']
    list_filter = ['category', 'brand', 'is_globally_active']
    search_fields = ['name', 'slug', 'description', 'variants__sku', 'variants__name'] 
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductAttributeValueInline, ProductVariantInline, ProductTagMapInline]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    change_list_template = 'admin/products/product_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-products/', self.admin_site.admin_view(self.import_products), 
                name='import_products'),
        ]
        return custom_urls + urls

    def import_products(self, request):
        if request.method == 'POST':
            form = ProductImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    file_type = form.cleaned_data['file_type']
                    import_file = form.cleaned_data['import_file']
                    update_existing = form.cleaned_data['update_existing']
                    
                    if file_type == 'csv':
                        csv_file = TextIOWrapper(import_file.file, encoding='utf-8-sig')
                        reader = csv.DictReader(csv_file)
                        data = list(reader)
                    else:  # JSON
                        json_data = import_file.read().decode('utf-8-sig')
                        data = json.loads(json_data)
                        if not isinstance(data, list):
                            data = [data]
                    
                    # Basic import logic
                    with transaction.atomic():
                        for item in data:
                            # Implement your import logic here
                            pass
                            
                    self.message_user(request, "Successfully imported products", messages.SUCCESS)
                    return redirect('..')
                    
                except Exception as e:
                    self.message_user(request, f"Error during import: {str(e)}", messages.ERROR)
        else:
            form = ProductImportForm()
        
        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Import Products',
        }
        return TemplateResponse(request, 'admin/products/product_import.html', context)

# --- Register Related Models ---

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug']
    list_filter = ['parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(ProductSegment)
class ProductSegmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title', 'slug']
    prepopulated_fields = {"slug": ("title",)}
    ordering = ['order']