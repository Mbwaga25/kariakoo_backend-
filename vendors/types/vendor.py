import graphene
from graphene_django import DjangoObjectType
from ..models import Vendor, ProductVendor, SponsorInstitutionVendor, ServiceProvider, ProductImage


# --- Base Vendor Type ---
class VendorType(DjangoObjectType):
    class Meta:
        model = Vendor
        fields = '__all__'

    def resolve_transactions(self, info):
        return self.transactions.all()


# --- Sponsor Institution Vendor Type ---
class SponsorInstitutionVendorType(DjangoObjectType):
    class Meta:
        model = SponsorInstitutionVendor
        fields = '__all__'


# --- Service Provider Type ---
class ServiceProviderType(DjangoObjectType):
    class Meta:
        model = ServiceProvider
        fields = '__all__'


# --- Product Image Type ---
class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "uploaded_at")


# --- Product Vendor Type with Related Images ---
class ProductVendorType(DjangoObjectType):
    product_images = graphene.List(ProductImageType)

    class Meta:
        model = ProductVendor
        fields = (
            "id",
            "product_name",
            "product_description",
            "unit_price",
            "stock_quantity",
            "vendor",
        )

    def resolve_product_images(self, info):
        return self.images.all()  # Using related_name 'images' from model
