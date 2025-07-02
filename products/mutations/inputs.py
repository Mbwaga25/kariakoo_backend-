import graphene
import graphene_file_upload.scalars


class ProductCategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    slug = graphene.String()
    description = graphene.String()
    parent_id = graphene.ID()
    image =graphene_file_upload.scalars.Upload

class ProductSegmentInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    slug = graphene.String()
    order = graphene.Int()
    is_active = graphene.Boolean()
    product_ids = graphene.List(graphene.ID)
