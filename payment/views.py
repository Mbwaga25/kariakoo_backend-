import os
import json
import logging
from datetime import datetime

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from payment.models import PaymentTransaction, TransactionStatus


def setup_payment_logger():
    """Initializes and configures the payment logger."""
    log_directory = "logs/payment/callback"
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


def log_callback_event(reference: str, payload: dict, level: str = "info"):
    """
    Log a callback event using the configured logger.
    """
    message = f"REF: {reference} - PAYLOAD: {json.dumps(payload)}"
    if level == "info":
        payment_logger.info(message)
    elif level == "error":
        payment_logger.error(message)
    elif level == "warning":
        payment_logger.warning(message)
    else:
        payment_logger.debug(message)


@csrf_exempt
@require_POST
def payment_callback(request):
    try:
        data = json.loads(request.body)

        reference = data.get("ThirdPartyReference")
        status = data.get("TransactionStatus")
        transaction_id = data.get("TransID")
        amount = data.get("Amount")
        result_type = data.get("ResultType")
        hash_value = data.get("Hash")

        if not reference or not status:
            return JsonResponse({"message": "Missing reference or status."}, status=400)

        try:
            transaction = PaymentTransaction.objects.get(reference=reference)
        except PaymentTransaction.DoesNotExist:
            log_callback_event(reference or "unknown", {"error": "Transaction not found", "data": data}, level="error")
            return JsonResponse({"message": "Transaction not found."}, status=404)

        # Normalize status
        normalized_status = status.strip().lower()
        if normalized_status == "sucess":  # typo fix from gateway
            normalized_status = TransactionStatus.SUCCESS
        elif normalized_status == "failed":
            normalized_status = TransactionStatus.FAILED
        else:
            normalized_status = TransactionStatus.PENDING

        # Save fields to DB
        transaction.status = normalized_status
        transaction.result_type = result_type
        transaction.transaction_id = transaction_id
        transaction.gateway_amount = amount or transaction.amount
        transaction.gateway_hash = hash_value
        transaction.response_data = data
        transaction.save()

        # Log success
        log_callback_event(reference, data)

        return JsonResponse({"message": "Transaction updated successfully."})

    except json.JSONDecodeError:
        log_callback_event("invalid-json", {"error": "Invalid JSON", "body": request.body.decode("utf-8")}, level="error")
        return JsonResponse({"message": "Invalid JSON."}, status=400)

    except Exception as e:
        log_callback_event("internal-error", {"error": str(e)}, level="error")
        return JsonResponse({"message": "Internal server error."}, status=500)
