import requests
import hashlib
from datetime import datetime

def send_payment_request(api_source, api_to, amount, product, callbackStatus, user, mobileNo, reference,callback):
    endpoint = "https://vodaapi.evmak.com/evpay-sandbox/collection/"
    
    current_date = datetime.now().strftime("%d-%m-%Y")
    hash_string = f"{user}|{current_date}"
    generated_hash = hashlib.md5(hash_string.encode()).hexdigest()

    payload = {
        "api_source": api_source,
        "api_to": api_to,
        "amount": amount,
        "product": product,
        "callbackStatus": callbackStatus,
        "callback":callback,
        "hash": generated_hash,
        "user": user,
        "mobileNo": mobileNo,
        "reference": reference,
        "callbackstatus": "Success"  # Note: This is duplicate with different case (callbackStatus above)
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"  # Explicitly ask for JSON response
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # This will raise for 4XX/5XX status codes
        
        # Try to parse JSON regardless of content-type header
        try:
            json_response = response.json()
            return {
                "order_id": json_response.get("order_id"),
                "amount": json_response.get("amount"),
                "response_code": json_response.get("response_code", 200),  # Default to 200 if not provided
                "response_desc": json_response.get("response_desc", "Success")
            }
        except ValueError:  # Includes simplejson and json.decoder.JSONDecodeError
            return {
                "order_id": None,
                "amount": None,
                "response_code": 403,
                "response_desc": f"Invalid JSON response: {response.text[:200]}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "order_id": None,
            "amount": None,
            "response_code": 403,
            "response_desc": str(e)
        }