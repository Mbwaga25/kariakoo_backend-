import graphene
from graphene_file_upload.scalars import Upload

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

    # ✅ Business Info
    businessCategory = graphene.String()
    retailWholesale = graphene.List(graphene.String)

    # ✅ Product Fields
    productName = graphene.String()
    productDescription = graphene.String()
    unitPrice = graphene.Float()
    stockQuantity = graphene.Int()
    productImage = graphene.List(Upload)

    # ✅ Sponsor Fields
    institutionName = graphene.String()
    package = graphene.String()
    partnershipInterest = graphene.String()
    orgRep = graphene.String()
    companyLogo = Upload()

    # ✅ Service Fields
    serviceName = graphene.String()
    serviceDescription = graphene.String()
    fixedPrice = graphene.Float()

    # ✅ Food Fields
    cuisineType = graphene.String()
    menuDescription = graphene.String()
    hasVegetarian = graphene.Boolean()
    hasVegan = graphene.Boolean()

    # ✅ Booth & Extra
    boothSize = graphene.String()
    powerNeeded = graphene.Boolean()
