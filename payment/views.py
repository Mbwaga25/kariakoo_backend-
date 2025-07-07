import os
import json
import logging
from datetime import datetime

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from payment.models import PaymentTransaction, TransactionStatus

LOG_BASE_DIR = os.path.join("log", "vendors", "callback")

def write_callback_log(reference: str, payload: dict):
    """
    Save callback payloads to a daily log file
    """
    os.makedirs(LOG_BASE_DIR, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"transaction-{date_str}.log"
    file_path = os.path.join(LOG_BASE_DIR, filename)

    with open(file_path, "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] REF: {reference} - PAYLOAD: {json.dumps(payload)}\n")


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
            write_callback_log(reference or "unknown", {"error": "Transaction not found", "data": data})
            return JsonResponse({"message": "Transaction not found."}, status=404)

        # Normalize status
        normalized_status = status.strip().lower()
        if normalized_status == "sucess":  # fix typo from gateway
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

        # Log for traceability
        write_callback_log(reference, data)

        return JsonResponse({"message": "Transaction updated successfully."})

    except json.JSONDecodeError:
        write_callback_log("invalid-json", {"error": "Invalid JSON", "body": request.body.decode("utf-8")})
        return JsonResponse({"message": "Invalid JSON."}, status=400)

    except Exception as e:
        write_callback_log("internal-error", {"error": str(e)})
        return JsonResponse({"message": "Internal server error."}, status=500)
