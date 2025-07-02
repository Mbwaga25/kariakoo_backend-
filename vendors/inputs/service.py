import graphene

class RegisterServiceProviderInput(graphene.InputObjectType):
    service_name = graphene.String(required=True)
    service_description = graphene.String(required=True)
    hourly_rate = graphene.Float(required=False)
    fixed_price = graphene.Float(required=False)
