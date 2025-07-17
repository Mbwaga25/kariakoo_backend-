import graphene
# import graphql_jwt # No longer directly needed here if JWT mutations are fully in UsersMutation

# Import Query and Mutation from each app's schema
from users.schema import Query as UsersQuery, Mutation as UsersMutation
from customers.schema import Query as CustomersQuery, Mutation as CustomersMutation
from products.schema import Query as ProductsQuery, Mutation as ProductsMutation
from stores.schema import Query as StoresQuery, Mutation as StoresMutation
from orders.schema import Query as OrdersQuery, Mutation as OrdersMutation
from ads.schema import Query as AdsQuery, Mutation as AdsMutation
from vendors.schema import VendorsQuery, VendorsMutation
from payment.schema import  PaymentMutation,PaymentQuery
import order_call.graphql.mutations 
import order_call.graphql.queries
from dashboard.DashboardQuery import DashboardQuery

class Query(
    UsersQuery,
    CustomersQuery,
    ProductsQuery,
    StoresQuery,
    OrdersQuery,
    VendorsQuery,
    AdsQuery,
    PaymentQuery,
    order_call.graphql.queries.Query,
    DashboardQuery,
    graphene.ObjectType,
):
    """Root query that combines queries from all applications."""
    pass

class Mutation(
    UsersMutation,         # Inherits all user-related and JWT authentication mutations
    CustomersMutation,
    ProductsMutation,
    StoresMutation,
    OrdersMutation,
    VendorsMutation, 
    AdsMutation,
    PaymentMutation,
    order_call.graphql.mutations.Mutation,
    graphene.ObjectType,
):
    """
    Root mutation that combines mutations from all applications.
    All JWT mutations are now handled within UsersMutation (users/mutations.py).
    """
    # Removed the explicit graphql_jwt fields here.
    # They are now inherited through UsersMutation.
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)