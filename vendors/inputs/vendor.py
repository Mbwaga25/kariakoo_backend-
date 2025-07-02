import graphene

class RegisterVendorInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    company_name = graphene.String(required=True)
    tin_number = graphene.String()
    contact_person = graphene.String(required=True)
    phone = graphene.String(required=True)
    vendor_type = graphene.String(required=True)