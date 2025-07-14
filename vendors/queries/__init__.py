import graphene

# --- Import the new, separate query classes ---
from .vendor import   VendorQuery
from  . ProductVendor import ProductVendorQuery
from  . SponsorInstitutionVendor import SponsorInstitutionVendorQuery

# The main Query class now inherits from all three separate query classes.
# This combines all their fields into a single root Query type.
class Query(
    ProductVendorQuery,
    SponsorInstitutionVendorQuery,
    VendorQuery,
    graphene.ObjectType
):
    """
    The root query for the application, combining all individual vendor queries.
    """
    pass

__all__ = ["Query"]