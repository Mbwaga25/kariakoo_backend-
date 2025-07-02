import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalar import Upload
from django.contrib.auth import authenticate
from graphql_jwt.shortcuts import get_token
from .models import Vendor, ProductVendor, FoodVendor, ServiceProvider, ProductImage

class VendorType(DjangoObjectType):
    class Meta:
        model = Vendor
        fields = '__all__'

class ProductVendorType(DjangoObjectType):
    images = graphene.List(lambda: ProductImageType)
    
    class Meta:
        model = ProductVendor
        fields = '__all__'
    
    def resolve_images(self, info):
        return self.images.all()

class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = '__all__'

class FoodVendorType(DjangoObjectType):
    class Meta:
        model = FoodVendor
        fields = '__all__'

class ServiceProviderType(DjangoObjectType):
    class Meta:
        model = ServiceProvider
        fields = '__all__'

class AuthPayload(graphene.ObjectType):
    token = graphene.String()
    vendor = graphene.Field(VendorType)

class RegisterVendorInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    company_name = graphene.String(required=True)
    tin_number = graphene.String()
    contact_person = graphene.String(required=True)
    phone = graphene.String(required=True)
    vendor_type = graphene.String(required=True)

class RegisterProductVendorInput(graphene.InputObjectType):
    product_name = graphene.String(required=True)
    product_description = graphene.String(required=True)
    unit_price = graphene.Decimal(required=True)
    stock_quantity = graphene.Int(required=True)
    images = graphene.List(Upload)

class RegisterFoodVendorInput(graphene.InputObjectType):
    cuisine_type = graphene.String(required=True)
    menu_description = graphene.String(required=True)
    has_vegetarian = graphene.Boolean()
    has_vegan = graphene.Boolean()

class RegisterServiceProviderInput(graphene.InputObjectType):
    service_name = graphene.String(required=True)
    service_description = graphene.String(required=True)
    hourly_rate = graphene.Decimal()
    fixed_price = graphene.Decimal()

class Query(graphene.ObjectType):
    vendors = graphene.List(VendorType)
    product_vendors = graphene.List(ProductVendorType)
    food_vendors = graphene.List(FoodVendorType)
    service_providers = graphene.List(ServiceProviderType)
    
    def resolve_vendors(self, info):
        return Vendor.objects.all()
    
    def resolve_product_vendors(self, info):
        return ProductVendor.objects.all()
    
    def resolve_food_vendors(self, info):
        return FoodVendor.objects.all()
    
    def resolve_service_providers(self, info):
        return ServiceProvider.objects.all()

class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    
    Output = AuthPayload
    
    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise Exception('Invalid credentials')
        
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            raise Exception('User is not a vendor')
        
        return AuthPayload(token=get_token(user), vendor=vendor)

class RegisterVendor(graphene.Mutation):
    class Arguments:
        input = RegisterVendorInput(required=True)
    
    Output = AuthPayload
    
    def mutate(self, info, input):
        from django.contrib.auth import get_user_model
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
        
        # Handle image uploads
        for image in input.images:
            ProductImage.objects.create(
                product=product_vendor,
                image=image
            )
        
        return product_vendor

class RegisterFoodVendor(graphene.Mutation):
    class Arguments:
        input = RegisterFoodVendorInput(required=True)
    
    Output = FoodVendorType
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            raise Exception('User is not a vendor')
        
        if vendor.vendor_type != 'food':
            raise Exception('User is not registered as a food vendor')
        
        food_vendor = FoodVendor(
            vendor=vendor,
            cuisine_type=input.cuisine_type,
            menu_description=input.menu_description,
            has_vegetarian=input.has_vegetarian or False,
            has_vegan=input.has_vegan or False,
        )
        food_vendor.save()
        
        return food_vendor

class RegisterServiceProvider(graphene.Mutation):
    class Arguments:
        input = RegisterServiceProviderInput(required=True)
    
    Output = ServiceProviderType
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            raise Exception('User is not a vendor')
        
        if vendor.vendor_type != 'service':
            raise Exception('User is not registered as a service provider')
        
        service_provider = ServiceProvider(
            vendor=vendor,
            service_name=input.service_name,
            service_description=input.service_description,
            hourly_rate=input.hourly_rate,
            fixed_price=input.fixed_price,
        )
        service_provider.save()
        
        return service_provider

class Mutation(graphene.ObjectType):
    login = Login.Field()
    register_vendor = RegisterVendor.Field()
    register_product_vendor = RegisterProductVendor.Field()
    register_food_vendor = RegisterFoodVendor.Field()
    register_service_provider = RegisterServiceProvider.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)