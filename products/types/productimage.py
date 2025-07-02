
# products/types/image.py
import graphene
from graphene_django import DjangoObjectType
from ..models import ProductImage

class ProductImageType(DjangoObjectType):
    image_url = graphene.String()

    class Meta:
        model = ProductImage
        fields = ("id", "image", "image_url", "alt_text", "is_primary", "order")

    def resolve_image_url(self, info):
        if self.image and hasattr(self.image, 'url'):
            return info.context.build_absolute_uri(self.image.url)
        return self.image_url or None # Fallback to the stored URLField if needed

# -------------------------------------------------