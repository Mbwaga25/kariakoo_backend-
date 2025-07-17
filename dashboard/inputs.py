# dashboard/inputs.py
import graphene
from .enums import GroupingEnum

class DashboardStatsInput(graphene.InputObjectType):
    status = graphene.String(required=False)
    vendor_type = graphene.String(required=False)
    date_from = graphene.Date(required=False)
    date_to = graphene.Date(required=False)
    group_by = GroupingEnum(required=False)  # NEW!
