import requests
import hashlib
from datetime import datetime
import os
import json

def ensure_payment_log_directory():
    """Ensure the payment logs directory exists, create it if not"""
    log_dir = "logs/payment/request/"  # Note: Using forward slash works on both Windows and Linux
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"Created payment logs directory at: {os.path.abspath(log_dir)}")
        return log_dir
    except Exception as e:
        print(f"Error creating payment logs directory: {e}")
        return None  # Fall back to current directory

def log_payment_transaction(log_dir, payload, response_data):
    """Log payment transaction details with timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"payment_{timestamp}_{response_data.get('response_code', 'error')}.json"
        
        log_path = os.path.join(log_dir, log_filename) if log_dir else log_filename
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": payload,
            "response": response_data,
            "status": "success" if response_data.get('response_code') == 200 else "failed"
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return True
    except Exception as e:
        print(f"Error logging payment transaction: {e}")
        return False

def send_payment_request(api_source, api_to, amount, product, user, mobileNo, reference, callback):
    endpoint = "https://vodaapi.evmak.com/prd/"
    current_date = datetime.now().strftime("%d-%m-%Y")
    hash_string = f"{user}|{current_date}"
    generated_hash = hashlib.md5(hash_string.encode()).hexdigest()

    payload = {
        "api_source": api_source,
        "api_to": api_to,
        "amount": amount,
        "product": product,
        "callback": callback,
        "hash": generated_hash,
        "user": user,
        "mobileNo": mobileNo,
        "reference": reference,
    }
    
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    response_template = {
        "order_id": None,
        "amount": None,
        "response_code": 500,
        "response_desc": "Internal Error"
    }

    try:
        # First ensure we can log before making the request
        log_dir = ensure_payment_log_directory()
        
        # Make the API request
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        try:
            json_response = response.json()
            response_data = {
                "order_id": json_response.get("order_id"),
                "amount": json_response.get("amount"),
                "response_code": json_response.get("response_code", 200),
                "response_desc": json_response.get("response_desc", "Success")
            }
        except ValueError as ve:
            response_data = {
                **response_template,
                "response_code": 422,
                "response_desc": f"Invalid JSON response: {str(ve)}"
            }

    except requests.exceptions.RequestException as re:
        response_data = {
            **response_template,
            "response_code": 403,
            "response_desc": f"Request failed: {str(re)}"
        }
    except Exception as e:
        response_data = {
            **response_template,
            "response_desc": f"Unexpected error: {str(e)}"
        }
    
    # Log the payment transaction
    log_payment_transaction(log_dir, payload, response_data)
    
    return response_data