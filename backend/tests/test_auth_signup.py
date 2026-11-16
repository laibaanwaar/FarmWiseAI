import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

from backend.core import config
from backend.core.security import hash_password, validate_password
from backend.main import app
from backend.repositories.user_repository import UserRepository
from backend.services import email_service
from backend.services.auth_service import (
    AuthService, InvalidVerificationCode, RateLimitExceeded,
)


GOOD_PASSWORD = "LongEnough!Password9"
GENERIC_MESSAGE = "If the address can receive verification, instructions will be sent shortly."


@pytest.fixture(autouse=True)
def otp_secret(monkeypatch):
    monkeypatch.setattr(config, "OTP_HMAC_SECRET", "test-only-hmac-key-0123456789abcdef")


@pytest.mark.parametrize("password", [
    "Short!A1", "alllowercasepassword1!", "ALLUPPERCASEPASSWORD1!",
    "NoDigitsHerePassword!", "NoPunctuationPassword123", "Has Space!Password123",
    "UnicodePasswordé123!", "password1234567890!",
    "A" * 129 + "a1!",
])
def test_password_policy_rejects_invalid_values(password):
    with pytest.raises(ValueError):
        validate_password(password)


def test_password_policy_hashes_exact_input_using_argon2id():
    from argon2 import PasswordHasher

    password_hash = hash_password(GOOD_PASSWORD)
    assert password_hash.startswith("$argon2id$")
    assert PasswordHasher().verify(password_hash, GOOD_PASSWORD)


class StubService:
    def __init__(self, failure=None):
        self.failure = failure
        self.calls = []

    def signup(self, *args):
        self.calls.append(args)
        if self.failure:
            raise self.failure

    def resend_verification(self, *args):
        self.calls.append(args)
        if self.failure:
            raise self.failure

    def verify_email(self, *args):
        self.calls.append(args)
        if self.failure:
            raise self.failure


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def set_service(service):
    app.state.auth_service = service


def test_malformed_json_is_safe_422(client):
    response = client.post("/api/v1/auth/signup", content='{"name":')
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}


@pytest.mark.parametrize("body", [
    {"name": "Test", "email": "not-an-email", "password": GOOD_PASSWORD},
    {"name": "Test", "email": "test@example.com", "password": GOOD_PASSWORD, "role": "admin"},
    {"name": "Test", "email": "test@example.com", "password": "weak", "role": "admin"},
])
def test_invalid_email_and_extra_fields_are_safe_422(client, body):
    secret = body["password"]
    response = client.post("/api/v1/auth/signup", json=body)
    assert response.status_code == 422
    assert secret not in response.text


def test_signup_returns_generic_202_and_normalizes_inputs(client):
    service = StubService()
    set_service(service)
    response = client.post("/api/v1/auth/signup", json={
        "name": "  Example User  ", "email": "  USER@Example.COM ", "password": GOOD_PASSWORD,
    })
    assert response.status_code == 202
    assert response.json() == {"message": GENERIC_MESSAGE}
    assert service.calls[0][:3] == ("Example User", "user@example.com", GOOD_PASSWORD)


def test_database_failure_is_generic_503_without_secrets(client):
    secret = "Mongo internal password is secret"
    set_service(StubService(ServerSelectionTimeoutError(secret)))
    response = client.post("/api/v1/auth/signup", json={
        "name": "Example", "email": "user@example.com", "password": GOOD_PASSWORD,
    })
    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable."}
    assert secret not in response.text


def test_signup_rate_limit_returns_429(client):
    set_service(StubService(RateLimitExceeded()))
    response = client.post("/api/v1/auth/signup", json={
        "name": "Example", "email": "user@example.com", "password": GOOD_PASSWORD,
    })
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many requests. Try again later."}


class AtomicUsers:
    def __init__(self):
        self.rows = {}
        self.lock = threading.Lock()

    def create_index(self, *args, **kwargs):
        return "uniq_user_email"

    def insert_one(self, document):
        with self.lock:
            if document["email"] in self.rows:
                raise DuplicateKeyError("duplicate")
            row = dict(document, _id=len(self.rows) + 1)
            self.rows[document["email"]] = row
            return type("Result", (), {"inserted_id": row["_id"]})()

    def find_one(self, query):
        row = self.rows.get(query["email"])
        return row if row and not row["email_verified"] else None


def test_concurrent_duplicate_inserts_create_only_one_account():
    collection = AtomicUsers()
    repository = UserRepository(collection)

    def create():
        return repository.create("Name", "same@example.com", "argon-hash")

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: create(), range(24)))
    assert sum(result is not None for result in results) == 1
    assert len(collection.rows) == 1
    assert collection.rows["same@example.com"]["role"] == "user"
    assert collection.rows["same@example.com"]["email_verified"] is False


class MemoryTokens:
    def __init__(self):
        self.entries = {}
        self.stored = []

    def delete_for_user(self, user_id):
        self.entries = {digest: entry for digest, entry in self.entries.items()
                        if entry["user_id"] != user_id}

    def store(self, user_id, otp_digest, ttl):
        entry = {"user_id": user_id,
                 "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl)}
        self.entries[otp_digest] = entry
        self.stored.append((user_id, otp_digest, ttl))

    def consume(self, otp_digest, user_id):
        entry = self.entries.get(otp_digest)
        if (not entry or entry["user_id"] != user_id
                or entry["expires_at"] <= datetime.now(timezone.utc)):
            return None
        del self.entries[otp_digest]
        return entry


class MemoryUsers:
    def __init__(self):
        self.by_email = {}

    def create(self, name, email, password_hash):
        if email in self.by_email:
            return None
        user = {"_id": "id1", "name": name, "email": email,
                "password_hash": password_hash, "role": "user", "email_verified": False}
        self.by_email[email] = user
        return user

    def find_pending_by_email(self, email):
        user = self.by_email.get(email)
        return user if user and not user["email_verified"] else None

    def mark_email_verified(self, user_id):
        for user in self.by_email.values():
            if user["_id"] == user_id and not user["email_verified"]:
                user["email_verified"] = True
                return True
        return False


def make_service(sender=lambda *_: None):
    users, tokens = MemoryUsers(), MemoryTokens()
    return AuthService(users, tokens, sender), users, tokens


def test_signup_and_resend_email_with_six_digit_code_without_links(monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, *args):
            pass

        def send_message(self, message):
            sent.append(message.get_content())

    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(config, "SMTP_FROM", "noreply@example.test")
    monkeypatch.setattr(config, "SMTP_USERNAME", "smtp-user")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "smtp-secret")
    monkeypatch.setattr(config, "SMTP_USE_TLS", True)
    service, _, tokens = make_service(email_service.send_verification_email)
    service.signup("Person", "person@example.com", GOOD_PASSWORD, "127.0.0.1")
    service.resend_verification("person@example.com", "127.0.0.2")

    assert len(sent) == 2
    for body in sent:
        assert re.search(r"(?<!\d)\d{6}(?!\d)", body)
        assert "http://" not in body and "https://" not in body
        assert "?token=" not in body and "verify-email" not in body
    assert len(tokens.stored) == 2
    assert all(len(digest) == 64 for _, digest, _ in tokens.stored)
    assert all(code not in " ".join(tokens.entries) for code in re.findall(r"\d{6}", " ".join(sent)))


def test_verify_email_accepts_leading_zero_and_consumes_code(monkeypatch):
    monkeypatch.setattr("backend.services.auth_service.new_email_otp", lambda: "012345")
    delivered = []
    service, users, tokens = make_service(lambda _, otp: delivered.append(otp))
    service.signup("Person", "person@example.com", GOOD_PASSWORD, "127.0.0.1")

    assert delivered == ["012345"]
    assert service.verify_email("person@example.com", "012345", "127.0.0.2")
    assert users.by_email["person@example.com"]["email_verified"] is True
    assert tokens.entries == {}
    with pytest.raises(InvalidVerificationCode):
        service.verify_email("person@example.com", "012345", "127.0.0.2")


def test_incorrect_code_does_not_consume_the_correct_code(monkeypatch):
    monkeypatch.setattr("backend.services.auth_service.new_email_otp", lambda: "123456")
    service, users, _ = make_service()
    service.signup("Person", "person@example.com", GOOD_PASSWORD, "127.0.0.1")

    with pytest.raises(InvalidVerificationCode):
        service.verify_email("person@example.com", "000000", "127.0.0.2")
    assert not users.by_email["person@example.com"]["email_verified"]
    assert service.verify_email("person@example.com", "123456", "127.0.0.2")


def test_expired_code_is_rejected(monkeypatch):
    monkeypatch.setattr("backend.services.auth_service.new_email_otp", lambda: "456789")
    monkeypatch.setattr(config, "EMAIL_OTP_TTL_SECONDS", -1)
    service, users, _ = make_service()
    service.signup("Person", "person@example.com", GOOD_PASSWORD, "127.0.0.1")

    with pytest.raises(InvalidVerificationCode):
        service.verify_email("person@example.com", "456789", "127.0.0.2")
    assert not users.by_email["person@example.com"]["email_verified"]


def test_verification_attempt_limit_is_enforced(monkeypatch):
    monkeypatch.setattr(config, "VERIFY_RATE_LIMIT", 1)
    monkeypatch.setattr("backend.services.auth_service.new_email_otp", lambda: "123456")
    service, _, _ = make_service()
    service.signup("Person", "person@example.com", GOOD_PASSWORD, "127.0.0.1")
    with pytest.raises(InvalidVerificationCode):
        service.verify_email("person@example.com", "000000", "127.0.0.2")
    with pytest.raises(RateLimitExceeded):
        service.verify_email("person@example.com", "123456", "127.0.0.2")


def test_resend_invalidates_previous_code(monkeypatch):
    codes = iter(("111111", "222222"))
    monkeypatch.setattr("backend.services.auth_service.new_email_otp", lambda: next(codes))
    service, users, _ = make_service()
    service.signup("Person", "person@example.com", GOOD_PASSWORD, "127.0.0.1")
    service.resend_verification("person@example.com", "127.0.0.2")

    with pytest.raises(InvalidVerificationCode):
        service.verify_email("person@example.com", "111111", "127.0.0.3")
    assert not users.by_email["person@example.com"]["email_verified"]
    assert service.verify_email("person@example.com", "222222", "127.0.0.3")


def test_verify_endpoint_accepts_six_digit_string_and_returns_no_otp(client):
    service = StubService()
    set_service(service)
    response = client.post("/api/v1/auth/verify-email", json={
        "email": "person@example.com", "otp": "012345",
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Email verified."}
    assert service.calls[0][:2] == ("person@example.com", "012345")
    assert "012345" not in response.text


def test_verify_endpoint_rejects_wrong_shape(client):
    set_service(StubService())
    response = client.post("/api/v1/auth/verify-email", json={
        "email": "person@example.com", "otp": 12345,
    })
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}


def test_verify_endpoint_maps_invalid_code_and_attempt_limit(client):
    for failure, expected in ((InvalidVerificationCode(), 400), (RateLimitExceeded(), 429)):
        set_service(StubService(failure))
        response = client.post("/api/v1/auth/verify-email", json={
            "email": "person@example.com", "otp": "000001",
        })
        assert response.status_code == expected
        assert "000001" not in response.text
