# yourapp/types/payment.py
import graphene

class PaymentResponseType(graphene.ObjectType):
    order_id = graphene.String()
    amount = graphene.Int()
    response_code = graphene.Int()
    response_desc = graphene.String()