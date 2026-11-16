import smtplib
from email.message import EmailMessage

from backend.core import config


def send_verification_email(recipient, otp):
    if not (config.SMTP_HOST and config.SMTP_FROM):
        return False
    message = EmailMessage()
    message["Subject"] = "Your FarmWise AI verification code"
    message["From"] = config.SMTP_FROM
    message["To"] = recipient
    message.set_content(
        f"Your FarmWise AI verification code is: {otp}\n\n"
        "Enter this code in the app to verify your email address. "
        "If you did not request this, you can ignore this message."
    )
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
        if config.SMTP_USE_TLS:
            server.starttls()
        if config.SMTP_USERNAME:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(message)
    return True
