import graphene
from ..models import ProductVendor, ProductImage,Vendor
from ..inputs.product import RegisterProductVendorInput
from ..types.product import ProductVendorType

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
        
        # Handle image uploads
        for image in input.images:
            ProductImage.objects.create(
                product=product_vendor,
                image=image
            )
        
        return product_vendor