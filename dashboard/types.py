import graphene

class ProductVendorStatsType(graphene.ObjectType):
    total = graphene.Int()
    accepted = graphene.Int()
    rejected = graphene.Int()
    pending = graphene.Int()

class BoothVendorStatsType(graphene.ObjectType):
    total = graphene.Int()
    paid = graphene.Int()
    failed = graphene.Int()
    pending = graphene.Int()

class SponsorStatsType(graphene.ObjectType):
    total = graphene.Int()
    accepted = graphene.Int()
    on_processing = graphene.Int()

class GroupedDataType(graphene.ObjectType):
    period = graphene.String()
    count = graphene.Int()

class ProductVendorDetailType(graphene.ObjectType):
    id = graphene.ID()
    product_name = graphene.String()
    status = graphene.String()
    unit_price = graphene.Float()
    stock_quantity = graphene.Int()
    vendor_name = graphene.String()
    created_at = graphene.String()

class BoothVendorDetailType(graphene.ObjectType):
    id = graphene.ID()
    company_name = graphene.String()
    vendor_type = graphene.String()
    phone = graphene.String()
    contact_person = graphene.String()
    is_approved = graphene.Boolean()
    registration_date = graphene.String()
    services = graphene.List(lambda: ServiceProviderDetailType)
    payments = graphene.List(lambda: PaymentTransactionDetailType)

class SponsorDetailType(graphene.ObjectType):
    id = graphene.ID()
    institution_name = graphene.String()
    status = graphene.String()
    package = graphene.String()
    partnership_interest = graphene.String()
    org_rep = graphene.String()
    vendor_name = graphene.String()
    created_at = graphene.String()

class PaymentTransactionDetailType(graphene.ObjectType):
    id = graphene.ID()
    reference = graphene.String()
    amount = graphene.Float()
    status = graphene.String()
    vendor_name = graphene.String()
    payed_to = graphene.String()
    gateway_name = graphene.String()
    created_at = graphene.String()

class ServiceProviderDetailType(graphene.ObjectType):
    id = graphene.ID()
    service_name = graphene.String()
    service_description = graphene.String()
    hourly_rate = graphene.Float()
    fixed_price = graphene.Float()
    booth_size = graphene.String()
    power_needed = graphene.Boolean()
    vendor_name = graphene.String()

class DashboardStatsType(graphene.ObjectType):
    product_vendors = graphene.Field(ProductVendorStatsType)
    booth_vendors = graphene.Field(BoothVendorStatsType)
    sponsors = graphene.Field(SponsorStatsType)
    grouped_payments = graphene.List(GroupedDataType)
    product_vendor_details = graphene.List(ProductVendorDetailType)
    booth_vendor_details = graphene.List(BoothVendorDetailType)
    sponsor_details = graphene.List(SponsorDetailType)
    payment_transaction_details = graphene.List(PaymentTransactionDetailType)

class DashboardStatsInput(graphene.InputObjectType):
    status = graphene.String(required=False)
    vendor_type = graphene.String(required=False)
    date_from = graphene.Date(required=False)
    date_to = graphene.Date(required=False)
    group_by = graphene.String(required=False)

class Query(graphene.ObjectType):
    dashboard_stats = graphene.Field(
        DashboardStatsType,
        filters=DashboardStatsInput(required=False)
    )
