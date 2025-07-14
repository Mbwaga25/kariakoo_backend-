import graphene
import os
from datetime import datetime
import logging
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from ..models import Vendor, ProductVendor, SponsorInstitutionVendor, ServiceProvider, ProductImage
from payment.models import PaymentGateway, PaymentTransaction, TransactionStatus
from ..types.payment import PaymentResponseType
from ..helpers.evmak_payment_helper import send_payment_request
from ..inputs.vendor import FullVendorInput
from ..helpers.sms_service import SMSService
from ..helpers.email_service import EmailService

# --- Helper for Image Conversion ---
def convert_to_webp(image_file):
    try:
        img = Image.open(image_file)
        buffer = BytesIO()
        img.save(buffer, format='WEBP')
        return ContentFile(buffer.getvalue(), name=f"{os.path.splitext(image_file.name)[0]}.webp")
    except Exception as e:
        print(f"Error converting image to WebP: {e}")
        return image_file

# --- Setup for Structured Logging ---
def setup_payment_logger():
    log_directory = "logs/payment/payment_response"
    os.makedirs(log_directory, exist_ok=True)
    log_file = os.path.join(log_directory, f"payment-response-{datetime.now().strftime('%Y-%m-%d')}.log")

    logger = logging.getLogger('payment_logger')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

payment_logger = setup_payment_logger()

class RegisterFullVendor(graphene.Mutation):
    class Arguments:
        input = FullVendorInput(required=True)

    Output = PaymentResponseType

    def mutate(self, info, input):
        vendor = Vendor.objects.create(
            fullname=input.fullname,
            email=input.email,
            company_name=input.companyName,
            tin_number=input.tinNumber,
            contact_person=input.contactPerson,
            phone=input.phone,
            vendor_type=input.vendorType,
        )

        if input.vendorType.lower() == "product":
            product_vendor = ProductVendor.objects.create(
                vendor=vendor,
                product_name=input.productName,
                product_description=input.productDescription,
                unit_price=input.unitPrice,
                stock_quantity=input.stockQuantity,
            )

            if input.productImage:
                for image_file in input.productImage:
                    webp_image = convert_to_webp(image_file)
                    ProductImage.objects.create(
                        product=product_vendor,
                        image=webp_image
                    )

            SMSService().send_sms(
                msisdn=input.phone,
                message=f"Thank you for registering as a {vendor.vendor_type}. We have received your details."
            )
            EmailService.send_email(
                subject="Registration Confirmation",
                message=f"Hello {vendor.fullname},\n\nWe have successfully received your registration as a {vendor.vendor_type}.",
                recipient_email=input.email
            )

            return PaymentResponseType(
                order_id=f"PRODUCT-NO-PAYMENT-{vendor.id}",
                amount=0,
                response_code=200,
                response_desc="Product vendor registration is complete. No payment required."
            )

        elif input.vendorType.lower() == "sponsor":
            SponsorInstitutionVendor.objects.create(
                vendor=vendor,
                institution_name=input.institutionName,
                package=input.package,
                partnershipInterest=input.partnershipInterest,
                orgRep=input.orgRep,
                companyLogo=input.companyLogo
            )

            SMSService().send_sms(
                msisdn=input.phone,
                message=f"Thank you for registering as a {vendor.vendor_type}. We have received your details."
            )
            EmailService.send_email(
                subject="Registration Confirmation",
                message=f"Hello {vendor.fullname},\n\nWe have successfully received your registration as a {vendor.vendor_type}.",
                recipient_email=input.email
            )

            return PaymentResponseType(
                order_id=f"SPONSOR-NO-PAYMENT-{vendor.id}",
                amount=0,
                response_code=200,
                response_desc="Sponsor registration complete. No payment required."
            )

        elif input.vendorType.lower() == "vendor":
            service_provider = ServiceProvider.objects.create(
                vendor=vendor,
                service_name=input.serviceName,
                service_description=input.serviceDescription,
                fixed_price=input.fixedPrice or None,
                boothSize=input.boothSize,
                powerNeeded=input.powerNeeded,
                menu_description=input.menuDescription,
                package=input.package,
            )

            SMSService().send_sms(
                msisdn=input.phone,
                message=f"Thank you for registering as a {vendor.vendor_type}. We have received your details."
            )
            EmailService.send_email(
                subject="Registration Confirmation",
                message=f"Hello {vendor.fullname},\n\nWe have successfully received your registration as a {vendor.vendor_type}.",
                recipient_email=input.email
            )

            try:
                payment_gateway = PaymentGateway.objects.get(name__iexact=input.apiTo)
            except PaymentGateway.DoesNotExist:
                raise Exception(f"Payment gateway '{input.apiTo}' not found.")

            transaction = PaymentTransaction.objects.create(
                gateway=payment_gateway,
                user=None,
                payed_to=input.payedTo,
                reference=f"VENDOR-REG-{vendor.id}",
                amount=input.amount,
                status=TransactionStatus.PENDING
            )

            payment_response = send_payment_request(
                api_source="WEBHOSTTZ",
                api_to=input.apiTo,
                amount=input.amount,
                product=f"Vendor-{vendor.vendor_type}",
                callback="https://test.zamundaholdings.co.tz/payment/callback/",
                user="onevoice",
                mobileNo=input.payedTo,
                reference=transaction.reference,
            )

            payment_logger.info(f"Transaction Ref: {transaction.reference}, Response: {payment_response}")
            transaction.response_data = payment_response

            if payment_response.get("response_code") == 200:
                transaction.status = TransactionStatus.SUCCESS
                SMSService().send_sms(
                    msisdn=input.phone,
                    message=f"Asante kwa kufanya malipo ya {input.amount} TZS kwa usajili wa {vendor.vendor_type}. Ref: {transaction.reference}"
                )
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

        else:
            return PaymentResponseType(
                order_id=None,
                amount=0,
                response_code=400,
                response_desc="Invalid vendor type provided."
            )
