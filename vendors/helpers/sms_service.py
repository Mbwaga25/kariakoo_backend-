import logging
import requests

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.user = 'osbornexhb'
        self.password = 'h1umhybu'
        self.sender_id = 'UNT Solut'
        self.country_code = '255'
        self.api_url = 'http://mshastra.com/sendurl.aspx'

    def send_sms(self, msisdn: str, message: str):
        # Format phone number to international if starts with 0
        if msisdn.startswith('0'):
            msisdn = self.country_code + msisdn[1:]

        params = {
            'user': self.user,
            'pwd': self.password,
            'senderid': self.sender_id,
            'CountryCode': self.country_code,
            'mobileno': msisdn,
            'msgtext': message,
        }

        try:
            response = requests.get(self.api_url, params=params)

            if response.ok:
                logger.info(f'SMS sent successfully to {msisdn}')
            else:
                logger.error(f'Failed to send SMS. Response: {response.text}')
        except Exception as e:
            logger.error(f'Exception sending SMS to {msisdn}: {str(e)}')
