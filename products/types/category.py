import graphene
from graphene_django import DjangoObjectType
from ..models import ProductCategory

class ProductCategoryType(DjangoObjectType):
    children = graphene.List(graphene.NonNull(lambda: ProductCategoryType))

    class Meta:
        model = ProductCategory
        fields = ("id", "name", "slug", "description", "parent", "children", "image")

    def resolve_children(self, info):
        # The 'children' related_name on the model handles this automatically.
        return self.children.all()

# -------------------------------------------------
