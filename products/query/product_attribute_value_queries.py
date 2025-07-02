import graphene
from ..models import ProductAttributeValue
from ..types import ProductAttributeValueType

class ProductAttributeValueQueries(graphene.ObjectType):
    """
    GraphQL queries for retrieving product attribute values.
    """

    # Field to get ALL attribute values (the default list query)
    all_product_attribute_values = graphene.List(
        graphene.NonNull(ProductAttributeValueType),
        description="Retrieve every product attribute value in the system."
    )

    # Field to get attribute values filtered by a specific product
    product_attribute_values = graphene.List(
        graphene.NonNull(ProductAttributeValueType),
        product_id=graphene.ID(required=True, description="The ID of the product to filter by."),
        description="Retrieve all attribute values for a specific product."
    )
    
    # Field to get a single attribute value by its own ID
    product_attribute_value_by_id = graphene.Field(
        ProductAttributeValueType, 
        id=graphene.ID(required=True, description="The unique ID of the attribute value record."),
        description="Retrieve a single attribute value by its ID."
    )

    # --- Resolvers ---

    def resolve_all_product_attribute_values(self, info, **kwargs):
        """
        Resolver for the 'all_product_attribute_values' field.
        Returns all records, pre-fetching related data for efficiency.
        """
        # Using select_related is a performance optimization
        return ProductAttributeValue.objects.select_related('product', 'attribute').all()

    def resolve_product_attribute_values(self, info, product_id, **kwargs):
        """
        Resolver for the 'product_attribute_values' field.
        Returns records filtered by the provided product_id.
        """
        return ProductAttributeValue.objects.select_related('product', 'attribute').filter(product_id=product_id)
        
    def resolve_product_attribute_value_by_id(self, info, id, **kwargs):
        """
        Resolver for the 'product_attribute_value_by_id' field.
        Returns a single record matching the given primary key (ID).
        """
        try:
            return ProductAttributeValue.objects.get(pk=id)
        except ProductAttributeValue.DoesNotExist:
            return None
