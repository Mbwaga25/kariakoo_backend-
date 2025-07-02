import graphene
from ..models import ProductSegment
from ..types import ProductSegmentType

class SegmentQueries:
    """Product segment-related GraphQL queries"""
    
    all_segments = graphene.List(
        graphene.NonNull(ProductSegmentType),
        description="Retrieve all active product segments."
    )

    def resolve_all_segments(self, info, **kwargs):
        return ProductSegment.objects.filter(is_active=True).order_by("order")