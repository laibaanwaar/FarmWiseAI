import smtplib
from email.message import EmailMessage

from backend.core import config


def send_verification_email(recipient, token):
    if not (config.SMTP_HOST and config.SMTP_FROM and config.VERIFICATION_URL):
        return False
    message = EmailMessage()
    message["Subject"] = "Verify your FarmWise AI account"
    message["From"] = config.SMTP_FROM
    message["To"] = recipient
    message.set_content(
        "Use this link to verify your email address: "
        f"{config.VERIFICATION_URL.rstrip('/')}?token={token}\n"
        "If you did not request this, you can ignore this message."
    )
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
        if config.SMTP_USE_TLS:
            server.starttls()
        if config.SMTP_USERNAME:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(message)
    return True
