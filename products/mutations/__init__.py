import graphene
from .product_category import (
    CreateProductCategoryMutation,
    UpdateProductCategoryMutation,
    DeleteProductCategoryMutation,
)

from .product_brands import (
    CreateBrandMutation,
    UpdateBrandMutation,  
    DeleteBrandMutation,  
)


from .product_segment import (
    CreateProductSegmentMutation,
    UpdateProductSegmentMutation,
    DeleteProductSegmentMutation,
)

from .ProductAttributeValueType import(
    CreateProductAttributeValueMutation,
    UpdateProductAttributeValueMutation,
    DeleteProductAttributeValueMutation
)

from .ProductAttributeType import (
    CreateAttributeMutation,
    UpdateAttributeMutation,
    DeleteAttributeMutation
)

from .productTag import (
    CreateTagMutation,
    UpdateTagMutation,
    DeleteTagMutation
)

from .ProductVariant import (
    CreateProductVariantMutation,
    UpdateProductVariantMutation,
    DeleteProductVariantMutation
)

from .product import (
    CreateProductMutation,
    UpdateProductMutation,
    DeleteProductMutation
    )
from .log_product_view import LogProductView
from products.product_import_export.import_export import ProductImportExportMutations

class ProductCatalogMutations(ProductImportExportMutations, graphene.ObjectType):
    create_product_category = CreateProductCategoryMutation.Field()
    update_product_category = UpdateProductCategoryMutation.Field()
    delete_product_category = DeleteProductCategoryMutation.Field()

    create_product_segment = CreateProductSegmentMutation.Field()
    update_product_segment = UpdateProductSegmentMutation.Field()
    delete_product_segment = DeleteProductSegmentMutation.Field()

     # Mutations for Attribute
    create_attribute = CreateAttributeMutation.Field()
    update_attribute = UpdateAttributeMutation.Field()
    delete_attribute = DeleteAttributeMutation.Field()

    # Mutations for ProductAttributeValue (from previous request)
    create_product_attribute_value = CreateProductAttributeValueMutation.Field()
    update_product_attribute_value = UpdateProductAttributeValueMutation.Field()
    delete_product_attribute_value = DeleteProductAttributeValueMutation.Field()

    create_tag = CreateTagMutation.Field()
    update_tag = UpdateTagMutation.Field()
    delete_tag = DeleteTagMutation.Field()


    create_brand = CreateBrandMutation.Field()
    update_brand = UpdateBrandMutation.Field() 
    delete_brand = DeleteBrandMutation.Field() 

    create_product_variant = CreateProductVariantMutation.Field()
    update_product_variant = UpdateProductVariantMutation.Field()
    delete_product_variant = DeleteProductVariantMutation.Field()

    log_product_view = LogProductView.Field()

    create_product = CreateProductMutation.Field()
    update_product = UpdateProductMutation.Field()
    delete_product = DeleteProductMutation.Field()

    