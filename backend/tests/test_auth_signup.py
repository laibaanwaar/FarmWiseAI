import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

from backend.core.security import hash_password, validate_password
from backend.main import app
from backend.repositories.user_repository import UserRepository
from backend.services.auth_service import AuthService, RateLimitExceeded


GOOD_PASSWORD = "LongEnough!Password9"
GENERIC_MESSAGE = "If the address can receive verification, instructions will be sent shortly."


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


def test_signup_returns_same_202_message_and_normalizes_inputs(client):
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


def test_rate_limit_returns_429(client):
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
        self.stored = []

    def delete_for_user(self, user_id):
        self.stored.clear()

    def store(self, user_id, token_hash, ttl):
        self.stored.append((user_id, token_hash, ttl))


class MemoryUser:
    def create(self, name, email, password_hash):
        return {"_id": "id1", "name": name, "email": email,
                "password_hash": password_hash, "role": "user", "email_verified": False}

    def find_pending_by_email(self, email):
        return {"_id": "id1", "email": email, "email_verified": False}


def test_email_delivery_failure_is_retryable_and_token_storage_is_hashed():
    tokens = MemoryTokens()
    service = AuthService(MemoryUser(), tokens, lambda *_: (_ for _ in ()).throw(RuntimeError("secret")))
    service.signup("Name", "person@example.com", GOOD_PASSWORD, "127.0.0.1")
    assert len(tokens.stored) == 1
    assert len(tokens.stored[0][1]) == 64
    assert tokens.stored[0][1] != "secret"
    service.resend_verification("person@example.com", "127.0.0.2")
    assert len(tokens.stored) == 1


def test_resend_route_returns_same_generic_response(client):
    service = StubService()
    set_service(service)
    response = client.post("/api/v1/auth/resend-verification", json={"email": "USER@example.com"})
    assert response.status_code == 202
    assert response.json() == {"message": GENERIC_MESSAGE}
