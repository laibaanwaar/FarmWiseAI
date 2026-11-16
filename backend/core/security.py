import hashlib
import hmac
import re
import secrets
import string

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from backend.core.config import BLOCKLISTED_PASSWORDS

_password_hasher = PasswordHasher(type=Type.ID)
_dummy_password_hash = _password_hasher.hash("FarmWiseAI-Dummy-Password!2026")


class OTPSecretNotConfigured(RuntimeError):
    pass


def validate_password(password: str) -> str:
    if not isinstance(password, str) or not 15 <= len(password) <= 128:
        raise ValueError("Password does not meet the required policy.")
    if not password.isascii() or any(character.isspace() for character in password):
        raise ValueError("Password does not meet the required policy.")
    if not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password)
            and re.search(r"[0-9]", password)
            and any(character in string.punctuation for character in password)):
        raise ValueError("Password does not meet the required policy.")
    if password.casefold() in BLOCKLISTED_PASSWORDS:
        raise ValueError("Password does not meet the required policy.")
    return password


def hash_password(password: str) -> str:
    return _password_hasher.hash(validate_password(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(password, _dummy_password_hash)


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_email_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    from backend.core.config import OTP_HMAC_SECRET

    if not OTP_HMAC_SECRET:
        raise OTPSecretNotConfigured
    return hmac.new(
        OTP_HMAC_SECRET.encode("utf-8"), otp.encode("ascii"), hashlib.sha256
    ).hexdigest()
