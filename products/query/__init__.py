import graphene

# --- Your other query imports ---
from .category_queries import *
from .product_queries import *
from .tag_queries import *
from .brand_queries import *
from .attribute_queries import *
from .segment_queries import *
from .product_attribute_value_queries import *

class ProductCatalogQueries(
    CategoryQueries,
    ProductQueries,
    TagQueries,
    BrandQueries,
    AttributeQueries,
    SegmentQueries,
   ProductAttributeValueQueries,
    graphene.ObjectType,
):
    """Combined product catalog queries"""
    pass