from django.conf import settings
from django.core.mail import EmailMessage
import threading
import logging

logger = logging.getLogger(__name__)

def send_email_async(email):
    try:
        email.send(fail_silently=False)  # 🚨 NEVER silence errors
        logger.info("OTP email sent successfully")
    except Exception as e:
        logger.error(f"OTP email failed: {e}")
        raise  # ← VERY IMPORTANT

def send_otp_email(to_email, otp):
    subject = "Your OTP Code"
    message = f"Your OTP is: {otp}"

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
    )

    threading.Thread(
        target=send_email_async,
        args=(email,),
        daemon=True,
    ).start()
