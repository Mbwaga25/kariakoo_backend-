# stores/connections.py
import graphene
from .types import StoreProductType

class StoreProductConnection(graphene.Connection):
    class Meta:
        node = StoreProductType