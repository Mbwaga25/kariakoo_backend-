import graphene
from ..models import Attribute
from ..types import AttributeType

class AttributeQueries:
    """Attribute-related GraphQL queries"""
    
    all_attributes = graphene.List(
        graphene.NonNull(AttributeType),
        description="Retrieve all product attributes."
    )

    def resolve_all_attributes(self, info, **kwargs):
        return Attribute.objects.all()