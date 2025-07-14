import graphene
from ..models import Vendor, SponsorInstitutionVendor
from ..types.vendor import SponsorInstitutionVendorType
from ..types.payment import PaymentResponseType

class CreateSponsorInstitutionVendor(graphene.Mutation):
    """Mutation to create a SponsorInstitutionVendor."""
    class Arguments:
        fullname = graphene.String(required=True)
        email = graphene.String(required=True)
        companyName = graphene.String(required=True)
        tinNumber = graphene.String(required=True)
        contactPerson = graphene.String(required=True)
        phone = graphene.String(required=True)
        institutionName = graphene.String(required=True)
        package = graphene.String(required=True)
        partnershipInterest = graphene.String(required=True)
        orgRep = graphene.String(required=True)
        companyLogo = graphene.String() # Assuming logo upload is handled

    Output = PaymentResponseType

    def mutate(self, info, **input):
        vendor = Vendor.objects.create(
            fullname=input.get('fullname'),
            email=input.get('email'),
            company_name=input.get('companyName'),
            tin_number=input.get('tinNumber'),
            contact_person=input.get('contactPerson'),
            phone=input.get('phone'),
            vendor_type="sponsor",
        )

        SponsorInstitutionVendor.objects.create(
            vendor=vendor,
            institution_name=input.get('institutionName'),
            package=input.get('package'),
            partnershipInterest=input.get('partnershipInterest'),
            orgRep=input.get('orgRep'),
            companyLogo=input.get('companyLogo')
        )

        return PaymentResponseType(
            order_id="SPONSOR-NO-PAYMENT",
            amount=0,
            response_code=200,
            response_desc="Sponsor registration complete. No payment required."
        )

class SponsorInstitutionVendorQuery(graphene.ObjectType):
    all_sponsor_institution_vendors = graphene.List(SponsorInstitutionVendorType)

    def resolve_all_sponsor_institution_vendors(self, info):
        return SponsorInstitutionVendor.objects.all()