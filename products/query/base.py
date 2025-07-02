import graphene
from graphql import GraphQLError
from django.db.models import Q, QuerySet
from django.apps import apps

# Assuming ProductType is defined in a way that it can be resolved
# by the time the schema is fully built.
# from ..types import ProductType 

class BaseProductQueries:
    """
    Holds the key features and helper functions for building product queries.
    This base class centralizes filtering, sorting, and pagination logic.
    """

    @staticmethod
    def get_product_queryset() -> QuerySet:
        """
        Returns the base queryset for products with prefetched and selected related data
        for performance optimization.
        """
        Product = apps.get_model('products', 'Product')
        return Product.objects.filter(is_globally_active=True).prefetch_related(
            'images',
            'tags',
            'attribute_values__attribute',
            'variants',
            'store_listings__store',
            'similar_products'
        ).select_related('category', 'brand')

    @staticmethod
    def _get_category_and_children_ids(slugs: list[str]) -> list[int]:
        """
        Helper method to retrieve the IDs of categories matching the provided slugs
        and all of their recursive descendants. This is the key to hierarchical filtering.
        """
        ProductCategory = apps.get_model('products', 'ProductCategory')
        if not slugs:
            return []

        # Use prefetch_related to optimize the upcoming lookups in the loop
        initial_categories = ProductCategory.objects.filter(slug__in=slugs).prefetch_related('children')
        
        if not initial_categories:
            return []

        all_category_ids = set()
        # Create a queue of categories to process
        categories_to_process = list(initial_categories)
        
        while categories_to_process:
            current_category = categories_to_process.pop(0)
            
            # Add the current category's ID to the final set
            all_category_ids.add(current_category.id)
            
            # Add all of its children to the queue to be processed
            for child in current_category.children.all():
                if child.id not in all_category_ids:
                    # We add the full child object to the queue to process its children later
                    categories_to_process.append(child)
                    
        return list(all_category_ids)

    @staticmethod
    def apply_product_filters(queryset, **filters):
        """Applies a set of filters to the product queryset."""
        
        search_term = filters.get("search")
        category_slugs = filters.get("category_slugs")
        brand_slugs = filters.get("brand_slugs")
        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        attribute_slugs = filters.get("attribute_slugs")
        tag_slugs = filters.get("tag_slugs")

        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term)
            )

        if category_slugs:
            # ✅ UPDATED LOGIC: Use the recursive helper to get all child category IDs
            all_matching_ids = BaseProductQueries._get_category_and_children_ids(category_slugs)
            if all_matching_ids:
                queryset = queryset.filter(category_id__in=all_matching_ids)
            else:
                # If no categories match the initial slugs, return an empty result
                return queryset.none()

        if brand_slugs:
            Brand = apps.get_model('products', 'Brand')
            brand_ids = Brand.objects.filter(slug__in=brand_slugs).values_list('id', flat=True)
            if brand_ids.exists():
                queryset = queryset.filter(brand_id__in=list(brand_ids))
            else:
                return queryset.none()

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if attribute_slugs:
            Attribute = apps.get_model('products', 'Attribute')
            attr_ids = Attribute.objects.filter(slug__in=attribute_slugs).values_list('id', flat=True)
            if attr_ids.exists():
                queryset = queryset.filter(attribute_values__attribute_id__in=list(attr_ids)).distinct()
            else:
                return queryset.none()
        
        if tag_slugs:
            Tag = apps.get_model('products', 'Tag')
            tag_ids = Tag.objects.filter(slug__in=tag_slugs).values_list('id', flat=True)
            if tag_ids.exists():
                queryset = queryset.filter(tags__id__in=list(tag_ids)).distinct()
            else:
                return queryset.none()

        return queryset

    @staticmethod
    def apply_product_sorting(queryset, sort_by=None, sort_order=None, search=None):
        """Applies sorting to the product queryset."""
        order_by_field = "-created_at" # Default sort

        if sort_by == "price":
            order_by_field = "price"
        elif sort_by == "rating":
            order_by_field = "-rating" # Default to desc
        elif sort_by == "name":
            order_by_field = "name"
        elif sort_by == "newest":
            order_by_field = "created_at"
        
        if sort_order == "desc" and not order_by_field.startswith('-'):
            order_by_field = f"-{order_by_field}"
        elif sort_order == "asc" and order_by_field.startswith('-'):
            order_by_field = order_by_field.lstrip('-')

        return queryset.order_by(order_by_field)

    @staticmethod
    def apply_pagination(queryset, limit=None, offset=None):
        """Applies pagination to the product queryset."""
        if offset is not None:
            queryset = queryset[offset:]
        if limit is not None:
            queryset = queryset[:limit]
        return queryset
