import graphene
from .vendor import RegisterFullVendor

class Mutation(graphene.ObjectType):
    register_vendor = RegisterFullVendor.Field()
    # initiate_vendor_payment = InitiateVendorPayment.Field()
