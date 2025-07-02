import graphene

class RegisterFoodVendorInput(graphene.InputObjectType):
    cuisine_type = graphene.String(required=True)
    menu_description = graphene.String(required=True)
    has_vegetarian = graphene.Boolean(required=False)
    has_vegan = graphene.Boolean(required=False)
