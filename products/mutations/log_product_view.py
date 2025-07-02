import graphene
from ..models import Product
from ..types import LogProductViewType

class LogProductView(graphene.Mutation):
    class Arguments:
        slug = graphene.String(required=True)

    Output = LogProductViewType

    def mutate(self, info, slug):
        try:
            product = Product.objects.get(slug=slug)
            product.views = (product.views or 0) + 1
            product.save(update_fields=['views'])
            return LogProductViewType(success=True, message=f"View logged for product: {slug}")
        except Product.DoesNotExist:
            return LogProductViewType(success=False, message=f"Product with slug '{slug}' not found.")
        except Exception as e:
            return LogProductViewType(success=False, message=str(e))
