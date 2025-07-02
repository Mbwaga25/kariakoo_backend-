import graphene
from graphql import GraphQLError
from django.db.models import Q
from django.apps import apps
from ..types import ProductType 
class BaseProductQueries:
    @staticmethod
    def get_product_queryset():
        """Returns the base queryset for products, potentially with select_related/prefetch_related"""
        # Example: Include related fields for efficient querying
        # Replace `Product` with your actual Django Product model
       
        Product = apps.get_model('products', 'Product')

        return Product.objects.prefetch_related(
            'images',
            'variants',
            'attribute_values__attribute',
            'tags',
            'store_listings', 
            # 'related_products' # Assuming related_products is a ManyToMany or similar field
        ).select_related('category', 'brand').all()

    @staticmethod
    def apply_product_filters(queryset, **filters):
        """Applies filters to the product queryset."""
        if filters.get("search"):
            search_term = filters["search"]
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term)
            )

        if filters.get("category_slugs"): # Changed from category_slug to category_slugs
            queryset = queryset.filter(category__slug__in=filters["category_slugs"])

        if filters.get("brand_slugs"): # Changed from brand_slug to brand_slugs
            queryset = queryset.filter(brand__slug__in=filters["brand_slugs"])

        if filters.get("min_price") is not None:
            queryset = queryset.filter(price__gte=filters["min_price"])

        if filters.get("max_price") is not None:
            queryset = queryset.filter(price__lte=filters["max_price"])

        if filters.get("attribute_slugs"): # New filter for attribute slugs
            # This logic depends on how your AttributeValue model is structured
            # Assuming AttributeValue has a 'slug' field derived from its value, or
            # you need to filter by attribute.slug and attribute_value.value
            attribute_slugs = filters["attribute_slugs"]
            # Example: Filter products that have at least one of the specified attribute values/slugs
            # This might require a distinct() or a more complex query depending on your exact schema
            queryset = queryset.filter(attribute_values__attribute__slug__in=attribute_slugs).distinct() # This is a basic example, adjust for your needs
            # If attribute_slugs represent attribute_value.slug (e.g., 'red', 'xl')
            # queryset = queryset.filter(attribute_values__slug__in=attribute_slugs).distinct()

        if filters.get("tag_slugs"): # New filter for tag slugs
            queryset = queryset.filter(tags__slug__in=filters["tag_slugs"]).distinct()


        return queryset

    @staticmethod
    def apply_product_sorting(queryset, sort_by=None, sort_order=None, search=None):
        """Applies sorting to the product queryset."""
        if sort_by:
            # Map frontend sort_by values to Django model fields
            order_by_field = None
            if sort_by == "price":
                order_by_field = "price"
            elif sort_by == "rating":
                order_by_field = "-rating" # Default to desc for rating
            elif sort_by == "name":
                order_by_field = "name"
            elif sort_by == "newest": # Assuming a 'created_at' or 'published_at' field
                order_by_field = "-created_at" # Or '-published_at'
            # 'relevance' is usually handled by search engines or a custom score

            if order_by_field:
                # Apply sort order if specified
                if sort_order == "desc" and not order_by_field.startswith('-'):
                    order_by_field = f"-{order_by_field}"
                elif sort_order == "asc" and order_by_field.startswith('-'):
                     order_by_field = order_by_field.lstrip('-')

                queryset = queryset.order_by(order_by_field)

        # Fallback to relevance for search if specific sort not provided
        if search and not sort_by: # Or if sort_by is 'relevance'
            # You might have a more complex relevance sorting based on full-text search
            # For simplicity, if search is present, sort by name or ID
            queryset = queryset.order_by('name') # or '-id' or a search relevance score
        
        return queryset

    @staticmethod
    def apply_pagination(queryset, limit=None, offset=None):
        """Applies pagination to the product queryset."""
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]
        return queryset


class ProductQueries(graphene.ObjectType):
    """Product-related GraphQL queries"""

    # Renamed to match frontend's consolidated query name and arguments
    all_products = graphene.List(
        graphene.NonNull(ProductType),
        offset=graphene.Int(description="Offset for pagination"),
        limit=graphene.Int(description="Limit the number of results"),
        min_price=graphene.Float(description="Minimum price filter", default_value=None),
        max_price=graphene.Float(description="Maximum price filter", default_value=None),
        category_slugs=graphene.List(graphene.String, description="Filter products by category slugs", default_value=[]),
        brand_slugs=graphene.List(graphene.String, description="Filter products by brand slugs", default_value=[]),
        attribute_slugs=graphene.List(graphene.String, description="Filter products by attribute slugs (e.g., 'color-red')", default_value=[]),
        tag_slugs=graphene.List(graphene.String, description="Filter products by tag slugs", default_value=[]),
        search=graphene.String(description="Search term to filter products by name or description", default_value=None),
        sort_by=graphene.String(description="Field to sort by (e.g., 'price', 'rating', 'name', 'newest')", default_value=None),
        sort_order=graphene.String(description="Sort order: 'asc' or 'desc'", default_value="desc"),
        description="Retrieve all products with advanced filtering, sorting and pagination."
    )

    # New field to get the total count of products matching filters (without pagination)
    total_product_count = graphene.Int(
        min_price=graphene.Float(description="Minimum price filter", default_value=None),
        max_price=graphene.Float(description="Maximum price filter", default_value=None),
        category_slugs=graphene.List(graphene.String, description="Filter products by category slugs", default_value=[]),
        brand_slugs=graphene.List(graphene.String, description="Filter products by brand slugs", default_value=[]),
        attribute_slugs=graphene.List(graphene.String, description="Filter products by attribute slugs", default_value=[]),
        tag_slugs=graphene.List(graphene.String, description="Filter products by tag slugs", default_value=[]), 
        search=graphene.String(description="Search term to filter products by name or description", default_value=None),
        description="Get the total count of products matching specific filters."
    )

    product_by_id_or_slug = graphene.Field(
        ProductType,
        id=graphene.ID(description="Get product by ID", required=False),
        slug=graphene.String(description="Get product by slug", required=False),
        description="Retrieve a single product by either ID or slug (must provide one)."
    )

    products_by_ids_or_slugs = graphene.List(
        graphene.NonNull(ProductType),
        ids=graphene.List(graphene.ID, required=False),
        slugs=graphene.List(graphene.String, required=False),
        description="Retrieve multiple products by IDs or slugs"
    )

    def resolve_all_products(self, info, **kwargs):
        try:
            queryset = BaseProductQueries.get_product_queryset()

            # Pass all relevant filter arguments to apply_product_filters
            # Frontend sends lists for slugs, ensure consistency
            filters = {
                "search": kwargs.get("search"),
                "category_slugs": kwargs.get("category_slugs", []),
                "brand_slugs": kwargs.get("brand_slugs", []),
                "attribute_slugs": kwargs.get("attribute_slugs", []),
                "tag_slugs": kwargs.get("tag_slugs", []),
                "min_price": kwargs.get("min_price"),
                "max_price": kwargs.get("max_price"),
            }

            sorting = {
                "sort_by": kwargs.get("sort_by"),
                "sort_order": kwargs.get("sort_order"),
                "search": kwargs.get("search"), # Pass search for relevance sorting
            }

            pagination = {
                "limit": kwargs.get("limit"),
                "offset": kwargs.get("offset"),
            }

            # Apply filters first
            filtered_queryset = BaseProductQueries.apply_product_filters(queryset, **filters)
            
            # Then apply sorting
            sorted_queryset = BaseProductQueries.apply_product_sorting(filtered_queryset, **sorting)

            # Finally apply pagination
            return BaseProductQueries.apply_pagination(sorted_queryset, **pagination)

        except Exception as e:
            raise GraphQLError(f"Error fetching products: {str(e)}")
            
    def resolve_total_product_count(self, info, **kwargs):
        """Resolves the total count of products matching filters without pagination."""
        try:
            queryset = BaseProductQueries.get_product_queryset()

            filters = {
                "search": kwargs.get("search"),
                "category_slugs": kwargs.get("category_slugs", []),
                "brand_slugs": kwargs.get("brand_slugs", []),
                "attribute_slugs": kwargs.get("attribute_slugs", []),
                "tag_slugs": kwargs.get("tag_slugs", []),
                "min_price": kwargs.get("min_price"),
                "max_price": kwargs.get("max_price"),
            }
            
            filtered_queryset = BaseProductQueries.apply_product_filters(queryset, **filters)
            return filtered_queryset.count()

        except Exception as e:
            raise GraphQLError(f"Error counting products: {str(e)}")

    def resolve_product_by_id_or_slug(self, info, id=None, slug=None):
        # ... (Your existing implementation for product_by_id_or_slug)
        try:
            if not id and not slug:
                raise GraphQLError("You must provide either an ID or a slug")

            queryset = BaseProductQueries.get_product_queryset()

            if id:
                product = queryset.filter(pk=id).first()
                if not product:
                    raise GraphQLError(f"Product with ID {id} not found")
                return product

            product = queryset.filter(slug=slug).first()
            if not product:
                raise GraphQLError(f"Product with slug '{slug}' not found")
            return product

        except Exception as e:
            raise GraphQLError(f"Error fetching product: {str(e)}")

    def resolve_products_by_ids_or_slugs(root, info, ids=None, slugs=None):
        # ... (Your existing implementation for products_by_ids_or_slugs)
        try:
            if not ids and not slugs:
                raise GraphQLError("You must provide at least one ID or slug")
            queryset = BaseProductQueries.get_product_queryset()

            filters = Q()
            if ids:
                filters |= Q(pk__in=ids)
            if slugs:
                filters |= Q(slug__in=slugs)
            return queryset.filter(filters).distinct()

        except Exception as e:
            raise GraphQLError(f"Error fetching products: {str(e)}")