import graphene
from ..models import Vendor, ProductVendor, SponsorInstitutionVendor,ServiceProvider,ProductImage
from payment.models import PaymentGateway, PaymentTransaction, TransactionStatus
from ..types.payment import PaymentResponseType
from ..helpers.evmak_payment_helper import send_payment_request
from ..inputs.vendor import FullVendorInput
from ..helpers.sms_service import SMSService
from ..helpers.email_service import EmailService

class RegisterFullVendor(graphene.Mutation):
    class Arguments:
        input = FullVendorInput(required=True)

    Output = PaymentResponseType

    def mutate(self, info, input):
        # Step 1: Create Vendor
        vendor = Vendor.objects.create(
            fullname=input.fullname,
            email=input.email,
            company_name=input.companyName,
            tin_number=input.tinNumber,
            contact_person=input.contactPerson,
            phone=input.phone,
            vendor_type=input.vendorType,
        )

        # Step 2: Create subtype
        if input.vendorType.lower() == "product":
            # Step 1: Create and save the product vendor
            product_vendor = ProductVendor.objects.create(
                vendor=vendor,
                product_name=input.productName,
                product_description=input.productDescription,
                unit_price=input.unitPrice,
                stock_quantity=input.stockQuantity,
            )

        if input.productImage:
            for image_file in input.productImage:
                ProductImage.objects.create(
                    product=product_vendor,
                    image=image_file
                )

        elif input.vendorType.lower() == "sponsor":
            SponsorInstitutionVendor.objects.create(
                vendor=vendor,
                institution_name=input.institutionName,
                package=input.package,
                partnershipInterest=input.partnershipInterest,
                orgRep=input.orgRep,
                # partnershipInterest =input.partnershipInterest,
                companyLogo=input.companyLogo
            )

            # ✅ Skip payment for sponsor — return early
            return PaymentResponseType(
                order_id="SPONSOR-NO-PAYMENT",
                amount=0,
                response_code=200,
                response_desc="Sponsor registration complete. No payment required."
            )

        elif input.vendorType.lower() == "vendor":
            ServiceProvider.objects.create(
                vendor=vendor,
                service_name=input.serviceName,
                service_description=input.serviceDescription,
                fixed_price=input.fixedPrice or None,
                boothSize=input.boothSize,
                powerNeeded=input.powerNeeded,
                menu_description=input.menuDescription,
                package=input.package,
                
            )

        # Step 3: Get payment gateway
        try:
            payment_gateway = PaymentGateway.objects.get(name__iexact=input.apiTo)
        except PaymentGateway.DoesNotExist:
            raise Exception(f"Payment gateway '{input.apiTo}' not found.")

        # Step 4: Create transaction
        transaction = PaymentTransaction.objects.create(
            gateway=payment_gateway,
            user=None,
            payed_to=input.payedTo,
            reference=f"VENDOR-REG-{vendor.id}",
            amount=input.amount,
            status=TransactionStatus.PENDING
        )

        # Step 5: Send payment request
        payment_response = send_payment_request(
            api_source="WEBHOSTTZ",
            api_to=input.apiTo,
            amount=input.amount,
            product=f"Vendor-{vendor.vendor_type}",
            callback="https://api.kariakofestival.co.tz/payment/callback/",
            user="onevoice",
            mobileNo=input.payedTo,
            reference=transaction.reference,
            # callbackStatus="Success"
        )

        transaction.response_data = payment_response

        # Step 6: Process response
        if payment_response.get("response_code") == 200:
            transaction.status = TransactionStatus.SUCCESS
            transaction.save()

            # ✅ SMS
            SMSService().send_sms(
                msisdn=input.phone,
                message=f"Asante kwa kufanya malipo ya {input.amount} TZS kwa usajili wa {vendor.vendor_type}. Ref: {transaction.reference}"
            )

            # ✅ Email
            EmailService.send_email(
                subject="Uthibitisho wa Malipo - Vendor Registration",
                message=(
                    f"Hongera {vendor.fullname},\n\n"
                    f"Tumepokea malipo yako ya TZS {input.amount} kwa usajili kama {vendor.vendor_type}. "
                    f"Namba ya rejea: {transaction.reference}\n\n"
                    f"Asante kwa kushirikiana nasi."
                ),
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
