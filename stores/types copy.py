# stores/types.py

import graphene
from graphene_django import DjangoObjectType
from .models import Store, StoreProduct

class StoreProductType(DjangoObjectType):
    """
    Represents the 'through' model connecting a Product to a Store,
    including store-specific details like price and stock.
    """
    class Meta:
        model = StoreProduct
        interfaces = (graphene.relay.Node,)
        fields = (
            "id",
            "store",
            "product",
            "price",
            "original_price",
            "stock_quantity",
            "is_available",
            "sku",
            "updated_at",
        )
        # Add this to convert Django field names to GraphQL conventions
        convert_choices_to_enum = False

    # Explicitly define fields that need custom logic or documentation
    price = graphene.Float(description="Current selling price in the store")
    original_price = graphene.Float(
        description="Original price before discounts (if any)",
        required=False
    )

class StoreProductConnection(graphene.Connection):
    """A connection for paginating over StoreProductType with additional metadata."""
    class Meta:
        node = StoreProductType

    total_count = graphene.Int()
    
    def resolve_total_count(self, info, **kwargs):
        return self.length

class StoreType(DjangoObjectType):
    """Represents a Store with all its details and associated products."""
    products = graphene.ConnectionField(
        StoreProductConnection,
        is_available=graphene.Boolean(
            default_value=True,
            description="Filter products by their availability in this store."
        ),
        description="List of products available in this store with store-specific pricing"
    )

    class Meta:
        model = Store
        interfaces = (graphene.relay.Node,)
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "email",
            "phone_number",
            "address_line1",
            "address_line2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "owner",
            "is_active",
            "opening_hours",
            "store_type",
            "created_at",
            "updated_at",
        )
        convert_choices_to_enum = False

    def resolve_products(self, info, is_available=True, **kwargs):
        """
        Custom resolver for products with optimized queries.
        Uses Django's prefetch_related to minimize database hits.
        """
        queryset = StoreProduct.objects.filter(
            store=self,
            is_available=is_available
        ).select_related('product').order_by('product__name')

        # Add pagination support
        if 'first' in kwargs:
            queryset = queryset[:kwargs['first']]
        if 'after' in kwargs:
            # Implement cursor-based pagination logic here
            pass

        return queryset

    # Add computed fields if needed
    formatted_address = graphene.String(
        description="Combined address in a single string"
    )
    
    def resolve_formatted_address(self, info):
        """Combine address components into a formatted string"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        return ", ".join(filter(None, parts))