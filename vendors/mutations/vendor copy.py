import graphene
from ..models import Vendor, ProductVendor, SponsorInstitutionVendor
from payment.models import PaymentGateway, PaymentTransaction, TransactionStatus
from ..types.payment import PaymentResponseType
from ..helpers.evmak_payment_helper import send_payment_request
from ..inputs.vendor import FullVendorInput
from ..helpers.sms_service import SMSService  
from ..helpers.email_service import  EmailService

class RegisterFullVendor(graphene.Mutation):
    class Arguments:
        input = FullVendorInput(required=True)

    Output = PaymentResponseType

    def mutate(self, info, input):
        # Step 1: Create Vendor
        vendor = Vendor.objects.create(
            fullname=input.fullname,
            email=input.email,
            company_name=input.company_name,
            tin_number=input.tinNumber,
            contact_person=input.contactPerson,
            phone=input.phone,
            vendor_type=input.vendorType,
        )

        # Step 2: Get payment gateway
        try:
            payment_gateway = PaymentGateway.objects.get(name__iexact=input.api_to)
        except PaymentGateway.DoesNotExist:
            raise Exception(f"Payment gateway '{input.api_to}' not found.")

        # Step 3: Create transaction
        transaction = PaymentTransaction.objects.create(
            gateway=payment_gateway,
            user=None,
            payedTo=input.payedTo,  
            reference=f"VENDOR_REG_{vendor.id}",
            amount=input.amount,
            status=TransactionStatus.PENDING
        )

        # Step 4: Create subtype
        if input.vendorType == "product":
            ProductVendor.objects.create(
                vendor=vendor,
                product_name=input.product_name,
                product_description=input.product_description,
                unit_price=input.unit_price,
                stock_quantity=input.stock_quantity,
            )
        elif input.vendorType == "sponsor":
            SponsorInstitutionVendor.objects.create(
                vendor=vendor,
                institution_name=input.institution_name,
                package=input.package,
            )

        # Step 5: Send payment request
        payment_response = send_payment_request(
            api_source="WEBHOSTTZ",
            api_to=input.api_to,
            amount=input.amount,
            product=f"Vendor-{vendor.vendor_type}",
            callback="https://webhook.site/your-unique-callback-url",
            user="onevoice",
            mobileNo=input.payedTo,
            reference=transaction.reference,
            callbackStatus="Success"
        )

        transaction.response_data = payment_response

        # Step 6: Process response and send SMS if successful
        if payment_response.get("response_code") == 200:
            transaction.status = TransactionStatus.SUCCESS
            transaction.save()

            # ✅ Send SMS
            sms = SMSService()
            sms.send_sms(
                msisdn=input.phone,
                message=f"Asante kwa kufanya malipo ya {input.amount} TZS kwa usajili wa {vendor.vendor_type}. Ref: {transaction.reference}"
            )

             # ✅ Send Email
            EmailService.send_email(
                subject="Uthibitisho wa Malipo - Vendor Registration",
                message=f"Hongera {vendor.fullname},\n\n"
                        f"Tumepokea malipo yako ya TZS {input.amount} kwa usajili kama {vendor.vendor_type}. "
                        f"Namba ya rejea: {transaction.reference}\n\n"
                        f"Asante kwa kushirikiana nasi.",
                recipient_email=input.email
            )

        else:
            transaction.status = TransactionStatus.FAILED
            transaction.save()

        return PaymentResponseType(
            order_id=payment_response.get("order_id"),
            amount=payment_response.get("amount"),
            response_code=payment_response.get("response_code", 403),
            response_desc=payment_response.get("response_desc", "Unknown error occurred")
        )
