# products/types/__init__.py
# This file makes the types in this directory easily importable.
# You can now do `from products.types import ProductType, BrandType` etc.

from .attribute import AttributeType
from .attribute_value import ProductAttributeValueType
from .brand import BrandType
from .category import ProductCategoryType
from .productimage import ProductImageType
from .log import LogProductViewType
from .product import ProductType
from .segment import ProductSegmentType
from .tag import TagType
from .variant import ProductVariantType

__all__ = [
    'AttributeType',
    'ProductAttributeValueType',
    'BrandType',
    'ProductCategoryType',
    'ProductImageType',
    'LogProductViewType',
    'ProductType',
    'ProductSegmentType',
    'TagType',
    'ProductVariantType',
]

# -------------------------------------------------
