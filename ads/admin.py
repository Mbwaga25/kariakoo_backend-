from django.contrib import admin
from .models import Page, Section, Ad, Attribute, AdAttributeValue

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "page")

class AdAttributeValueInline(admin.TabularInline):
    model = AdAttributeValue
    extra = 1  # Number of empty rows to show

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "active")
    list_filter = ("section", "active")
    inlines = [AdAttributeValueInline]

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(AdAttributeValue)
class AdAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("ad", "attribute", "value")
    list_filter = ("attribute",)
