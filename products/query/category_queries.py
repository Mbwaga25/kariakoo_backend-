import graphene
from graphql import GraphQLError
from django.apps import apps
from ..models import ProductCategory, Product
from ..types import ProductCategoryType, ProductType
from .base import BaseProductQueries  # Assuming base.py contains BaseProductQueries

class CategoryQueries(graphene.ObjectType):
    """Category-related GraphQL queries"""

    all_categories = graphene.List(
        graphene.NonNull(ProductCategoryType),
        level=graphene.Int(description="Filter categories by their nesting level (0 for top-level)."),
        description="Retrieve all product categories, optionally filtered by level."
    )

    category_by_id_or_slug = graphene.Field(
        ProductCategoryType,
        id=graphene.ID(required=False),
        slug=graphene.String(required=False),
        description="Retrieve a single product category by its ID or slug."
    )

    products_by_category = graphene.List(
        graphene.NonNull(ProductType),
        category_slug=graphene.String(required=True),
        description="Retrieve products belonging to a specific category and all its descendants."
    )

    @staticmethod
    def _get_self_and_all_children_ids(slugs: list[str]) -> list[int]:
        """
        Helper method to retrieve the IDs of categories matching the provided slugs
        and all of their recursive descendants. This is efficient for handling
        nested category structures.
        """
        ProductCategory = apps.get_model('products', 'ProductCategory')
        
        if not slugs:
            return []

        initial_categories = ProductCategory.objects.filter(slug__in=slugs)
        
        all_category_ids = set(initial_categories.values_list('id', flat=True))
        categories_to_check = list(initial_categories)
        
        while categories_to_check:
            parent_category = categories_to_check.pop(0)
            children = parent_category.children.all()
            for child in children:
                if child.id not in all_category_ids:
                    all_category_ids.add(child.id)
                    categories_to_check.append(child)
                    
        return list(all_category_ids)

    def resolve_all_categories(self, info, level=None, **kwargs):
        queryset = ProductCategory.objects.all().prefetch_related('children')
        if level == 0:
            queryset = queryset.filter(parent__isnull=True)
        return queryset

    def resolve_category_by_id_or_slug(self, info, id=None, slug=None, **kwargs):
        if id:
            return ProductCategory.objects.filter(pk=id).first()
        if slug:
            return ProductCategory.objects.filter(slug=slug).first()
        return None

    def resolve_products_by_category(self, info, category_slug, **kwargs):
        """
        Fetches products for a given category slug, including products
        from all of its descendant categories.
        """
        try:
            # ✅ CORRECTED: Call the helper method directly on the class (CategoryQueries)
            # This avoids the NoneType error by not relying on the 'self' instance.
            all_category_ids = CategoryQueries._get_self_and_all_children_ids(slugs=[category_slug])

            if not all_category_ids:
                return Product.objects.none()

            product_queryset = BaseProductQueries.get_product_queryset()
            return product_queryset.filter(category_id__in=all_category_ids)

        except Exception as e:
            raise GraphQLError(f"An error occurred while fetching products for category '{category_slug}': {str(e)}")

