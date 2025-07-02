from orders.models import Transaction
import uuid

def initiate_payment(order, payment_method):
    return Transaction.objects.create(
        order=order,
        transaction_id=str(uuid.uuid4()),
        amount=order.calculate_total(),
        payment_method=payment_method,
        status='pending'
    )

def complete_payment(transaction, status, response_data=None):
    transaction.status = status
    transaction.response_data = response_data or {}
    transaction.save(update_fields=["status", "response_data"])
