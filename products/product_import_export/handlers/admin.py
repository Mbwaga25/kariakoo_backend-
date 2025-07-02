from django.contrib import admin
from django import forms
from ...models import Product
from ..helpers import handle_image_import
import csv
import json

class ProductImportForm(forms.Form):
    file_type = forms.ChoiceField(choices=[('csv', 'CSV'), ('json', 'JSON')])
    import_file = forms.FileField()
    update_existing = forms.BooleanField(required=False, help_text="Update existing products")
    create_related = forms.BooleanField(required=False, initial=True, help_text="Create related models if they don't exist")

class ProductAdmin(admin.ModelAdmin):
    change_list_template = 'admin/product_change_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-products/', self.import_products, name='import-products'),
        ]
        return custom_urls + urls
    
    def import_products(self, request):
        if request.method == 'POST':
            form = ProductImportForm(request.POST, request.FILES)
            if form.is_valid():
                file_type = form.cleaned_data['file_type']
                import_file = form.cleaned_data['import_file']
                update_existing = form.cleaned_data['update_existing']
                create_related = form.cleaned_data['create_related']
                
                try:
                    if file_type == 'csv':
                        decoded_file = import_file.read().decode('utf-8')
                        reader = csv.DictReader(decoded_file.splitlines())
                        data = list(reader)
                    else:
                        decoded_file = import_file.read().decode('utf-8')
                        data = json.loads(decoded_file)
                    
                    # Process the data
                    handler = ProductHandler(update_existing, create_related)
                    for item in data:
                        handler.handle(item)
                    
                    self.message_user(request, "Products imported successfully")
                except Exception as e:
                    self.message_user(request, f"Error importing products: {str(e)}", level='error')
                
                return redirect('..')
        else:
            form = ProductImportForm()
        
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        return TemplateResponse(request, 'admin/product_import.html', context)

admin.site.register(Product, ProductAdmin)