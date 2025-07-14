import os
import logging
import requests

BIRQ_API_KEY = os.getenv("BIRQ_API_KEY", "")
BIRQ_SENDER_ID = os.getenv("BIRQ_SENDER_ID", "")

logger = logging.getLogger("sms_service")

def send_briq_sms(msisdn: str, message: str):
    url = "https://karibu.briq.tz/v1/message/send-instant"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": BIRQ_API_KEY
    }

    if msisdn.startswith("0"):
        msisdn = "255" + msisdn[1:]

    payload = {
        "content": message,
        "recipients": [msisdn],
        "sender_id": BIRQ_SENDER_ID
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.ok:
            logger.info(f"Briq SMS sent successfully to {msisdn}")
        else:
            logger.error(f"Failed to send Briq SMS to {msisdn}. Response: {response.text}")
    except Exception as e:
        logger.error(f"Exception sending Briq SMS to {msisdn}: {str(e)}")
