import graphene
from graphql_jwt.shortcuts import get_token
from django.contrib.auth import get_user_model
from ..models import Vendor
from ..inputs.vendor import RegisterVendorInput
from ..types.vendor import AuthPayload

class RegisterVendor(graphene.Mutation):
    class Arguments:
        input = RegisterVendorInput(required=True)
    
    Output = AuthPayload
    
    def mutate(self, info, input):
        User = get_user_model()
        user = User(
            username=input.username,
            email=input.email,
        )
        user.set_password(input.password)
        user.save()
        
        vendor = Vendor(
            user=user,
            company_name=input.company_name,
            tin_number=input.tin_number,
            contact_person=input.contact_person,
            phone=input.phone,
            vendor_type=input.vendor_type,
        )
        vendor.save()
        
        return AuthPayload(token=get_token(user), vendor=vendor)