import graphene
class FullVendorInput(graphene.InputObjectType):
    fullname = graphene.String()
    email = graphene.String()
    password = graphene.String()
    companyName = graphene.String(required=True)
    tinNumber = graphene.String()
    contactPerson = graphene.String(required=True)
    phone = graphene.String(required=True)
    amount = graphene.Float(required=True)
    apiTo = graphene.String(required=True)
    payedTo = graphene.String(required=True)
    vendorType = graphene.String(required=True)

    # Product
    productName = graphene.String()
    productDescription = graphene.String()
    unitPrice = graphene.Float()
    stockQuantity = graphene.Int()

    # Sponsor
    institutionName = graphene.String()
    package = graphene.String()

   # Service
    serviceName = graphene.String()
    serviceDescription = graphene.String()
    fixedPrice = graphene.Float()

    # Food
    cuisineType = graphene.String()
    menuDescription = graphene.String()
    hasVegetarian = graphene.Boolean()
    hasVegan = graphene.Boolean()

    # Extra (like booths)
    boothSize = graphene.String()
    powerNeeded = graphene.Boolean()