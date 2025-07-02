from .vendor import VendorQuery
from .product import ProductQuery
from .food import FoodServiceQuery
import graphene

class Query(FoodServiceQuery, graphene.ObjectType):
    pass
__all__ = ["VendorQuery", "ProductQuery"]
