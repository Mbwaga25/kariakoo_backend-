# products/types/product.py
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q, Prefetch
from ..models import Product
from stores.models import StoreProduct
from .tag import TagType

class ProductType(DjangoObjectType):
    availability_in_store = graphene.Field(
        'stores.types.StoreProductType',  # Using string reference
        store_id=graphene.ID(required=False),
        store_slug=graphene.String(required=False),
        description="Availability in specific store"
    )
    
    all_store_listings = graphene.List(
        graphene.NonNull('stores.types.StoreProductType'),
        description="All store listings for this product"
    )
    
    price = graphene.Float(
        description="Current price (lowest available if varies by store)"
    )
    
    rating = graphene.Float(
        description="Average product rating"
    )
    
    original_price = graphene.Float(
        description="Original price before discounts"
    )
    
    stock_quantity = graphene.Int(
        description="Total available stock across all stores"
    )
    
    category = graphene.Field(
        'products.types.category.ProductCategoryType',
        description="Product category"
    )
    
    brand = graphene.Field(
        'products.types.brand.BrandType',
        description="Product brand"
    )
    
    images = graphene.List(
        graphene.NonNull('products.types.productimage.ProductImageType'),
        description="Product images"
    )

    tags = graphene.List(graphene.NonNull(TagType))
    
    attribute_values = graphene.List(
        graphene.NonNull('products.types.attribute_value.ProductAttributeValueType'),
        description="Product attributes and values"
    )
    
    variants = graphene.List(
        graphene.NonNull('products.types.variant.ProductVariantType'),
        description="Product variants"
    )
    
    related_products = graphene.List(
        graphene.NonNull(lambda: ProductType),
        description="Related products from the same category"
    )
    
    similar_products = graphene.List(
        graphene.NonNull(lambda: ProductType),
        description="Similar products"
    )
    
    image = graphene.Field(
        'products.types.productimage.ProductImageType',
        description="Primary product image"
    )

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "category", "brand",
            "meta_title", "meta_description","meta_keywords", "is_globally_active",
            "created_at", "updated_at",
            "images", "attribute_values", "tags", "variants",            "images", "attribute_values", "tags", "variants",
            "price", "rating", "related_products", "similar_products",
            "stock_quantity",
        )
    
    def resolve_availability_in_store(self, info, store_id=None, store_slug=None):
        if not store_id and not store_slug:
            return None
            
        try:
            store_filter = Q(pk=store_id) if store_id else Q(slug=store_slug)
            store_product = (StoreProduct.objects
                .filter(product=self, store__is_active=True)
                .filter(store_filter)
                .select_related('store')
                .first()
            )
            return store_product
        except (StoreProduct.DoesNotExist, ValueError):
            return None

    def resolve_all_store_listings(self, info):
        return (StoreProduct.objects
                .filter(product=self, is_available=True, store__is_active=True)
                .select_related('store')
                .order_by('price'))

    def resolve_price(self, info):
        """Returns the lowest available price across all stores"""
        if hasattr(self, 'lowest_price'):
            return self.lowest_price
        return (StoreProduct.objects
                .filter(product=self, is_available=True)
                .order_by('price')
                .values_list('price', flat=True)
                .first())

    def resolve_images(self, info):
        if hasattr(self, 'prefetched_images'):
            return self.prefetched_images
        return self.images.all()
    
    def resolve_tags(self, info, **kwargs):
        return self.tags.all()        

    def resolve_attribute_values(self, info):
        if hasattr(self, 'prefetched_attributes'):
            return self.prefetched_attributes
        return (self.attribute_values
                .all()
                .select_related('attribute')
                .order_by('attribute__name'))

    def resolve_variants(self, info):
        if hasattr(self, 'prefetched_variants'):
            return self.prefetched_variants
        return (self.variants
                .filter(is_active=True)
                .select_related('product')
                .order_by('name'))

    def resolve_related_products(self, info):
        """
        FIX: This resolver now fetches other products from the same category,
        excluding the current product itself. This provides a sensible default
        for related items and avoids the 'related_products' attribute error.
        """
        if not self.category:
            return []
            
        return (Product.objects
                .filter(category=self.category, is_globally_active=True)
                .exclude(pk=self.pk)
                .order_by('?')[:8])

    def resolve_similar_products(self, info):
        # This logic is now identical to related_products. You may want to
        # differentiate them later, e.g., by using tags or other attributes.
        if hasattr(self, 'prefetched_similar'):
            return self.prefetched_similar
        
        if not self.category:
            return []

        return (Product.objects
                .filter(category=self.category, is_globally_active=True)
                .exclude(pk=self.pk)
                .order_by('?')[:8])

    def resolve_image(self, info):
        # FIX: Corrected a syntax error here.
        if hasattr(self, 'primary_image'):
            return self.primary_image
        # Tries to find a primary image, or falls back to the first available image.
        return self.images.filter(is_primary=True).first() or self.images.first()

