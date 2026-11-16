import hashlib
import re
import secrets
import string

from argon2 import PasswordHasher, Type

from backend.core.config import BLOCKLISTED_PASSWORDS

_password_hasher = PasswordHasher(type=Type.ID)


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


def new_verification_token():
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
