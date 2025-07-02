# stores/queries.py
import graphene
from django.db.models import F, ExpressionWrapper, DecimalField, Value
from django.db.models.functions import Power, Sin, Cos, Radians, ASin, Sqrt
from math import radians, sin, cos, sqrt, asin
from .models import Store, StoreProduct
from .types import StoreType, StoreProductType

class StoreQueries(graphene.ObjectType):
    # GET /stores
    all_stores = graphene.List(
        StoreType,
        is_active=graphene.Boolean(),
        city=graphene.String(),
        with_products=graphene.Boolean(default_value=False)
    )
    
    # GET /stores/:id (or by slug)
    store_by_id_or_slug = graphene.Field(
        StoreType,
        id=graphene.ID(required=False),
        slug=graphene.String(required=False),
        with_products=graphene.Boolean(default_value=False)
    )

    # GET /stores/nearby?lat=...&lng=...
    nearby_stores = graphene.List(
        StoreType,
        latitude=graphene.Float(required=True),
        longitude=graphene.Float(required=True),
        radius_km=graphene.Float(default_value=10.0),
        with_products=graphene.Boolean(default_value=False)
    )

    # GET /stores/:id/products
    products_in_store = graphene.List(
        StoreProductType,
        store_id=graphene.ID(required=False),
        store_slug=graphene.String(required=False),
        is_available=graphene.Boolean(default_value=True)
    )

    # GET /store-products?store_id=123&product_id=456
    store_product_details = graphene.Field(
        StoreProductType,
        store_id=graphene.ID(required=False),
        store_slug=graphene.String(required=False),
        product_id=graphene.ID(required=True)
    )

    def resolve_all_stores(self, info, is_active=None, city=None, with_products=False, **kwargs):
        queryset = Store.objects.all()
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        if with_products:
            queryset = queryset.prefetch_related('storeproduct_set__product')
        
        return queryset.order_by('name')

    def resolve_store_by_id_or_slug(self, info, id=None, slug=None, with_products=False, **kwargs):
        queryset = Store.objects.all()
        
        if id:
            queryset = queryset.filter(pk=id)
        elif slug:
            queryset = queryset.filter(slug=slug)
        else:
            return None
        
        store = queryset.first()
        
        if store and with_products:
            # Prefetch related products and include them in the store object
            store.products = StoreProduct.objects.filter(store=store).select_related('product')
        
        return store

    def resolve_nearby_stores(self, info, latitude, longitude, radius_km, with_products=False):
        """Finds stores within a given radius using Haversine formula."""
        radius_m = radius_km * 1000  # Convert km to meters
        earth_radius_m = 6371000

        queryset = Store.objects.filter(
            is_active=True, 
            latitude__isnull=False, 
            longitude__isnull=False
        )

        if with_products:
            queryset = queryset.prefetch_related('storeproduct_set__product')

        # Python-based distance calculation
        stores_with_distance = []
        R = 6371  # Earth radius in km
        lat1_rad = radians(latitude)
        lon1_rad = radians(longitude)

        for store in queryset:
            if store.latitude is None or store.longitude is None:
                continue
                
            lat2_rad = radians(float(store.latitude))
            lon2_rad = radians(float(store.longitude))
            
            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad
            
            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
            c = 2 * asin(sqrt(a))
            distance_km = R * c
            
            if distance_km <= radius_km:
                store.distance = distance_km
                stores_with_distance.append(store)
        
        return sorted(stores_with_distance, key=lambda s: s.distance)

    def resolve_products_in_store(self, info, store_id=None, store_slug=None, is_available=True, **kwargs):
        if not store_id and not store_slug:
            return StoreProduct.objects.none()
        
        queryset = StoreProduct.objects.filter(is_available=is_available)
        
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        elif store_slug:
            queryset = queryset.filter(store__slug=store_slug)
        
        return queryset.select_related('product', 'store')

    def resolve_store_product_details(self, info, product_id, store_id=None, store_slug=None, **kwargs):
        if not product_id or (not store_id and not store_slug):
            return None
        
        queryset = StoreProduct.objects.filter(product_id=product_id)
        
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        elif store_slug:
            queryset = queryset.filter(store__slug=store_slug)
        
        return queryset.select_related('product', 'store').first()

    