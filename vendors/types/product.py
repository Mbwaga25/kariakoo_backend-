import graphene
from graphene_django import DjangoObjectType
from ..models import ProductVendor, ProductImage

class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductVendorType(DjangoObjectType):
    images = graphene.List(ProductImageType)
    
    class Meta:
        model = ProductVendor
        fields = '__all__'
    
    def resolve_images(self, info):
        return self.images.all()