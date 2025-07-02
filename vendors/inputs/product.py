import graphene
from graphene_file_upload.scalars import Upload  

class RegisterProductVendorInput(graphene.InputObjectType):
    product_name = graphene.String(required=True)
    product_description = graphene.String(required=True)
    unit_price = graphene.Float(required=True)  
    stock_quantity = graphene.Int(required=True)
    images = graphene.List(Upload, required=False)
