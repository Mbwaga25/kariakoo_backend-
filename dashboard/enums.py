# dashboard/enums.py
import graphene

class GroupingEnum(graphene.Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
