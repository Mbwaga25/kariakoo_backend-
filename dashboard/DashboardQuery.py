import graphene
from dashboard.types import (
    DashboardStatsType, 
    ProductVendorStatsType, 
    BoothVendorStatsType, 
    SponsorStatsType, 
    DashboardStatsInput,
    GroupedDataType,
    ProductVendorDetailType,
    BoothVendorDetailType,
    SponsorDetailType,
    PaymentTransactionDetailType,
    ServiceProviderDetailType
)
from vendors.models import Vendor, ProductVendor, SponsorInstitutionVendor, ServiceProvider
from payment.models import PaymentTransaction
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

def get_grouped_payment_data(qs, group_by):
    if group_by == "day":
        trunc = TruncDay("created_at")
    elif group_by == "week":
        trunc = TruncWeek("created_at")
    elif group_by == "month":
        trunc = TruncMonth("created_at")
    else:
        trunc = TruncDay("created_at")

    return (
        qs.annotate(period=trunc)
          .values("period")
          .annotate(count=Count("id"))
          .order_by("period")
    )

class DashboardQuery(graphene.ObjectType):
    dashboard_stats = graphene.Field(
        DashboardStatsType,
        filters=DashboardStatsInput(required=False)
    )

    def resolve_dashboard_stats(self, info, filters=None):
        payment_qs = PaymentTransaction.objects.all()
        if filters:
            if filters.status:
                payment_qs = payment_qs.filter(status=filters.status)
            if filters.vendor_type:
                payment_qs = payment_qs.filter(vendor__vendor_type=filters.vendor_type)
            if filters.date_from and filters.date_to:
                payment_qs = payment_qs.filter(created_at__range=(filters.date_from, filters.date_to))

        grouped_data = get_grouped_payment_data(payment_qs, filters.group_by if filters else "day")

        product_vendors_list = [
            ProductVendorDetailType(
                id=pv.id,
                product_name=pv.product_name,
                status=pv.status,
                unit_price=float(pv.unit_price),
                stock_quantity=pv.stock_quantity,
                vendor_name=pv.vendor.company_name,
                created_at=pv.vendor.registration_date.isoformat()
            ) for pv in ProductVendor.objects.select_related('vendor').order_by('-vendor__registration_date')[:10]
        ]

        booth_vendors_list = []
        for bv in Vendor.objects.order_by('-registration_date')[:10]:
            services = [
                ServiceProviderDetailType(
                    id=sp.id,
                    service_name=sp.service_name,
                    service_description=sp.service_description,
                    hourly_rate=float(sp.hourly_rate) if sp.hourly_rate else None,
                    fixed_price=float(sp.fixed_price) if sp.fixed_price else None,
                    booth_size=sp.boothSize,
                    power_needed=sp.powerNeeded,
                    vendor_name=sp.vendor.company_name
                ) for sp in ServiceProvider.objects.filter(vendor=bv)
            ]
            payments = [
                PaymentTransactionDetailType(
                    id=pt.id,
                    reference=pt.reference,
                    amount=float(pt.amount),
                    status=pt.status,
                    vendor_name=pt.vendor.company_name if pt.vendor else None,
                    payed_to=pt.payed_to,
                    gateway_name=pt.gateway.name,
                    created_at=pt.created_at.isoformat()
                ) for pt in PaymentTransaction.objects.filter(vendor=bv)
            ]
            booth_vendors_list.append(
                BoothVendorDetailType(
                    id=bv.id,
                    company_name=bv.company_name,
                    vendor_type=bv.vendor_type,
                    phone=bv.phone,
                    contact_person=bv.contact_person,
                    is_approved=bv.is_approved,
                    registration_date=bv.registration_date.isoformat(),
                    services=services,
                    payments=payments
                )
            )

        sponsor_list = [
            SponsorDetailType(
                id=sp.id,
                institution_name=sp.institution_name,
                status=sp.status,
                package=sp.package,
                partnership_interest=sp.partnershipInterest,
                org_rep=sp.orgRep,
                vendor_name=sp.vendor.company_name,
                created_at=sp.vendor.registration_date.isoformat()
            ) for sp in SponsorInstitutionVendor.objects.select_related('vendor').order_by('-vendor__registration_date')[:10]
        ]

        payment_list = [
            PaymentTransactionDetailType(
                id=pt.id,
                reference=pt.reference,
                amount=float(pt.amount),
                status=pt.status,
                vendor_name=pt.vendor.company_name if pt.vendor else None,
                payed_to=pt.payed_to,
                gateway_name=pt.gateway.name,
                created_at=pt.created_at.isoformat()
            ) for pt in PaymentTransaction.objects.order_by('-created_at')[:10]
        ]

        return DashboardStatsType(
            product_vendors=ProductVendorStatsType(
                total=ProductVendor.objects.values('vendor_id').distinct().count(),
                accepted=ProductVendor.objects.filter(status="ACCEPTED").values('vendor_id').distinct().count(),
                rejected=ProductVendor.objects.filter(status="REJECTED").values('vendor_id').distinct().count(),
                pending=ProductVendor.objects.filter(status="PENDING").values('vendor_id').distinct().count(),
            ),
            booth_vendors=BoothVendorStatsType(
                total=Vendor.objects.count(),
                paid=PaymentTransaction.objects.filter(status="SUCCESS").values('vendor_id').distinct().count(),
                failed=PaymentTransaction.objects.filter(status="FAILED").values('vendor_id').distinct().count(),
                pending=PaymentTransaction.objects.filter(status="PENDING").values('vendor_id').distinct().count(),
            ),
            sponsors=SponsorStatsType(
                total=SponsorInstitutionVendor.objects.values('vendor_id').distinct().count(),
                accepted=SponsorInstitutionVendor.objects.filter(status="ACCEPTED").values('vendor_id').distinct().count(),
                on_processing=SponsorInstitutionVendor.objects.filter(status="ON_PROCESSING").values('vendor_id').distinct().count(),
            ),
            grouped_payments=[GroupedDataType(period=str(item["period"].date()), count=item["count"]) for item in grouped_data],
            product_vendor_details=product_vendors_list,
            booth_vendor_details=booth_vendors_list,
            sponsor_details=sponsor_list,
            payment_transaction_details=payment_list
        )
