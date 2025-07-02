import graphene
import graphql_jwt
# Import Query and Mutation from each app's schema
from users.schema import Query as UsersQuery, Mutation as UsersMutation
from customers.schema import Query as CustomersQuery, Mutation as CustomersMutation
from products.schema import Query as ProductsQuery, Mutation as ProductsMutation
from stores.schema import Query as StoresQuery, Mutation as StoresMutation
from orders.schema import Query as OrdersQuery, Mutation as OrdersMutation
from ads.schema import Query as AdsQuery, Mutation as AdsMutation

class Query(
    UsersQuery,
    CustomersQuery,
    ProductsQuery,
    StoresQuery,
    OrdersQuery,
    AdsQuery,
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
    AdsMutation,
    graphene.ObjectType,
):
    """
    Root mutation that combines mutations from all applications.
    All JWT mutations are now handled within UsersMutation (users/mutations.py).
    """
    pass

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    delete_token_cookie = graphql_jwt.DeleteJSONWebTokenCookie.Field()
    delete_refresh_token_cookie = graphql_jwt.DeleteRefreshTokenCookie.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)