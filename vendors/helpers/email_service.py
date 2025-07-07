from django.conf import settings
from django.core.mail import send_mail

class EmailService:
    @staticmethod
    def send_email(subject: str, message: str, recipient_email: str):
        try:
            from_email = f"{settings.EMAIL_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>"
            send_mail(
                subject,
                message,
                from_email,
                [recipient_email],
                fail_silently=False
            )
        except Exception as e:
            # log error
            pass
