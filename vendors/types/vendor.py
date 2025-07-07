import graphene
from graphene_django import DjangoObjectType
from ..models import Vendor

class VendorType(DjangoObjectType):
    vendor_type_display = graphene.String()

    class Meta:
        model = Vendor
        fields = '__all__'

    def resolve_vendor_type_display(self, info):
        return self.get_vendor_type_display()
