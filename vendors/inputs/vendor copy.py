import graphene

class FullVendorInput(graphene.InputObjectType):
    # General Info
    fullname = graphene.String()  # Used for vendors and sponsors
    email = graphene.String()
    # password = graphene.String()
    company_name = graphene.String(required=True)
    tin_number = graphene.String()
    contact_person = graphene.String(required=True)
    phone = graphene.String(required=True)
    payed_to= graphene.String(required=True)
    amount = graphene.Float(required=True)
    api_to = graphene.String(required=True)  # Gateway/payment method name
    vendor_type = graphene.String(required=True)

    # Product Vendor
    product_name = graphene.String()
    product_description = graphene.String()
    unit_price = graphene.Float()
    stock_quantity = graphene.Int()

    # Food Vendor
    cuisine_type = graphene.String()
    menu_description = graphene.String()
    has_vegetarian = graphene.Boolean()
    has_vegan = graphene.Boolean()

    # Service Vendor
    service_name = graphene.String()
    service_description = graphene.String()
    hourly_rate = graphene.Float()
    fixed_price = graphene.Float()

    # Sponsor Institution Vendor
    institution_name = graphene.String()
    package = graphene.String()
