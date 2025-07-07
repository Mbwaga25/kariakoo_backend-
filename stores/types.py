# stores/types.py

import graphene
from graphene_django import DjangoObjectType
from .models import Store, StoreProduct

# No direct import from 'products.types' to prevent circular dependencies.
# Graphene's type registry will handle the association.


class StoreProductType(DjangoObjectType):
    """
    Represents the 'through' model connecting a Product to a Store,
    including store-specific details like price and stock.
    """
    class Meta:
        model = StoreProduct
        interfaces = (graphene.relay.Node,)
        # Explicitly define fields for better clarity and security.
        # Graphene-Django automatically resolves ForeignKey fields (like 'product'
        # and 'store') to their corresponding GraphQL types.
        fields = (
            "id",
            "store",
            "product",
            # "price",
            # "original_price",
            # "stock_quantity",
            # "is_available",
            # "sku",
            # "updated_at",
        )


class StoreProductConnection(graphene.Connection):
    """A connection for paginating over StoreProductType."""
    class Meta:
        node = StoreProductType


class StoreType(DjangoObjectType):
    """Represents a Store."""
    products = graphene.List(
        graphene.NonNull(StoreProductType),
        is_available=graphene.Boolean(
            default_value=True,
            description="Filter products by their availability in this store."
        )
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

    def resolve_products(self, info, is_available=True):
        """
        Resolver for the 'products' field. It retrieves the list of
        products associated with this specific store.
        """
        # Querying the StoreProduct model to get store-specific product info.
        # .select_related('product') is a crucial performance optimization
        # to prevent N+1 query issues when accessing product details later.
        return StoreProduct.objects.filter(
            store=self,
            is_available=is_available
        ).select_related('product')
    
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