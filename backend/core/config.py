import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def env_int(name, default):
    try:
        return max(1, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


MONGODB_DB = os.getenv("MONGODB_DB", "farmwise_ai")
SIGNUP_RATE_LIMIT = env_int("AUTH_RATE_LIMIT", "5")
SIGNUP_RATE_WINDOW_SECONDS = env_int("AUTH_RATE_WINDOW_SECONDS", "900")
RESEND_RATE_LIMIT = env_int("AUTH_RESEND_RATE_LIMIT", "3")
RESEND_RATE_WINDOW_SECONDS = env_int("AUTH_RESEND_RATE_WINDOW_SECONDS", "900")
VERIFY_RATE_LIMIT = env_int("AUTH_VERIFY_RATE_LIMIT", "5")
VERIFY_RATE_WINDOW_SECONDS = env_int("AUTH_VERIFY_RATE_WINDOW_SECONDS", "900")
EMAIL_OTP_TTL_SECONDS = env_int("EMAIL_OTP_TTL_SECONDS", "600")
OTP_HMAC_SECRET = os.getenv("OTP_HMAC_SECRET", "")
LOGIN_RATE_LIMIT = env_int("AUTH_LOGIN_RATE_LIMIT", "5")
LOGIN_RATE_WINDOW_SECONDS = env_int("AUTH_LOGIN_RATE_WINDOW_SECONDS", "900")
ACCESS_TOKEN_TTL_SECONDS = env_int("ACCESS_TOKEN_TTL_SECONDS", "900")
SESSION_TTL_SECONDS = env_int("SESSION_TTL_SECONDS", "86400")
BLOCKLISTED_PASSWORDS = frozenset(
    value.casefold()
    for value in os.getenv(
        "BLOCKLISTED_PASSWORDS", "password,password123,123456789012345,"
        "qwertyuiopasdfg,letmein12345678"
    ).split(",")
    if value
)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = env_int("SMTP_PORT", "587")
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_FROM_EMAIL", ""))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").casefold() == "true"
