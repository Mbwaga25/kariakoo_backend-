import graphene
from graphql_jwt.shortcuts import get_token
from django.contrib.auth import get_user_model
from ..models import Vendor, ProductVendor, FoodVendor, ServiceProvider, ProductImage
from ..types.vendor import AuthPayload
from ..inputs.vendor import RegisterVendorInput
from ..inputs.product import RegisterProductVendorInput
from ..inputs.food import RegisterFoodVendorInput
from ..inputs.service import RegisterServiceProviderInput

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

class RegisterProductVendor(graphene.Mutation):
    class Arguments:
        input = RegisterProductVendorInput(required=True)
    
    Output = ProductVendorType
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            raise Exception('User is not a vendor')
        
        if vendor.vendor_type != 'product':
            raise Exception('User is not registered as a product vendor')
        
        product_vendor = ProductVendor(
            vendor=vendor,
            product_name=input.product_name,
            product_description=input.product_description,
            unit_price=input.unit_price,
            stock_quantity=input.stock_quantity,
        )
        product_vendor.save()
        
        for image in input.images:
            ProductImage.objects.create(
                product=product_vendor,
                image=image
            )
        
        return product_vendor

class VendorsMutation(graphene.ObjectType):
    register_vendor = RegisterVendor.Field()
    register_product_vendor = RegisterProductVendor.Field()
    # Add other vendor mutations here