import copy
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.core import config
from backend.core.security import hash_password, hash_token
from backend.main import app
from backend.services.auth_service import (
    AuthService, EmailNotVerified, InvalidCredentials, InvalidRefreshToken,
    RateLimitExceeded,
)


PASSWORD = "LongEnough!Password9"


class FakeUsers:
    def __init__(self, verified=True):
        self.user = {
            "_id": "user-1", "name": "Test User", "email": "user@example.com",
            "password_hash": hash_password(PASSWORD), "role": "user",
            "email_verified": verified,
        }

    def find_by_email(self, email):
        return copy.deepcopy(self.user) if email == self.user["email"] else None

    def find_by_id(self, user_id):
        return copy.deepcopy(self.user) if user_id == self.user["_id"] else None


class AtomicSessions:
    """Thread-safe test double matching the repository's conditional Mongo updates."""

    def __init__(self):
        self.rows = {}
        self.lock = threading.Lock()

    def create_session(self, user_id, access_hash, refresh_hash, access_expiry, deadline):
        row = {
            "_id": f"session-{len(self.rows) + 1}", "user_id": user_id,
            "access_token_hash": access_hash, "refresh_token_hash": refresh_hash,
            "rotated_refresh_token_hashes": [], "access_expires_at": access_expiry,
            "session_expires_at": deadline, "revoked": False, "revoked_at": None,
        }
        with self.lock:
            self.rows[row["_id"]] = row
        return copy.deepcopy(row)

    def find_active_by_refresh_hash(self, refresh_hash, now):
        with self.lock:
            for row in self.rows.values():
                if (row["refresh_token_hash"] == refresh_hash and not row["revoked"]
                        and row["session_expires_at"] > now):
                    return copy.deepcopy(row)
        return None

    def rotate_refresh(self, session_id, old_hash, access_hash, refresh_hash,
                       access_expiry, now):
        with self.lock:
            row = self.rows.get(session_id)
            if (not row or row["refresh_token_hash"] != old_hash or row["revoked"]
                    or row["session_expires_at"] <= now):
                return None
            row["rotated_refresh_token_hashes"].append(old_hash)
            row["access_token_hash"] = access_hash
            row["refresh_token_hash"] = refresh_hash
            row["access_expires_at"] = access_expiry
            return copy.deepcopy(row)

    def revoke_if_reused_refresh_hash(self, refresh_hash, now):
        with self.lock:
            for row in self.rows.values():
                if (refresh_hash in row["rotated_refresh_token_hashes"]
                        and not row["revoked"] and row["session_expires_at"] > now):
                    row["revoked"] = True
                    row["revoked_at"] = now
                    return True
        return False

    def find_active_by_access_hash(self, access_hash, now):
        with self.lock:
            for row in self.rows.values():
                if (row["access_token_hash"] == access_hash and not row["revoked"]
                        and row["session_expires_at"] > now):
                    return copy.deepcopy(row)
        return None

    def revoke(self, session_id, now):
        with self.lock:
            row = self.rows.get(session_id)
            if not row or row["revoked"]:
                return False
            row["revoked"] = True
            row["revoked_at"] = now
            return True


class BarrierSessions(AtomicSessions):
    def __init__(self):
        super().__init__()
        self.read_barrier = threading.Barrier(2)

    def find_active_by_refresh_hash(self, refresh_hash, now):
        row = super().find_active_by_refresh_hash(refresh_hash, now)
        self.read_barrier.wait(timeout=3)
        return row


class NoTokens:
    pass


def make_service(verified=True, sessions=None):
    users = FakeUsers(verified)
    sessions = sessions or AtomicSessions()
    service = AuthService(users, NoTokens(), lambda *_: None, sessions)
    return service, users, sessions


@pytest.fixture
def auth_config(monkeypatch):
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT", 5)
    monkeypatch.setattr(config, "LOGIN_RATE_WINDOW_SECONDS", 900)
    monkeypatch.setattr(config, "ACCESS_TOKEN_TTL_SECONDS", 900)
    monkeypatch.setattr(config, "SESSION_TTL_SECONDS", 86400)


def test_successful_login_returns_token_pair(auth_config):
    service, _, sessions = make_service()
    result = service.login("user@example.com", PASSWORD, "127.0.0.1")

    assert result["token_type"] == "bearer"
    assert result["access_token"] and result["refresh_token"]
    assert result["access_token"] != result["refresh_token"]
    session = next(iter(sessions.rows.values()))
    assert session["access_token_hash"] == hash_token(result["access_token"])
    assert session["refresh_token_hash"] == hash_token(result["refresh_token"])
    assert result["access_token"] not in str(session)
    assert result["refresh_token"] not in str(session)


def test_unknown_and_incorrect_password_share_generic_failure(auth_config):
    service, _, _ = make_service()
    with pytest.raises(InvalidCredentials):
        service.login("missing@example.com", PASSWORD, "127.0.0.1")
    with pytest.raises(InvalidCredentials):
        service.login("user@example.com", "WrongPassword!12345", "127.0.0.1")


def test_login_endpoint_returns_token_pair_and_generic_credential_errors(auth_config):
    service, users, sessions = make_service()
    app.state.auth_service = service
    app.state.user_repository = users
    app.state.auth_sessions = sessions
    with TestClient(app) as client:
        success = client.post("/api/v1/auth/login", json={
            "email": " USER@EXAMPLE.COM ", "password": PASSWORD,
        })
        wrong = client.post("/api/v1/auth/login", json={
            "email": "user@example.com", "password": "WrongPassword!12345",
        })
        unknown = client.post("/api/v1/auth/login", json={
            "email": "missing@example.com", "password": PASSWORD,
        })
    assert success.status_code == 200
    assert set(success.json()) == {"access_token", "refresh_token", "token_type", "expires_in"}
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert PASSWORD not in success.text


def test_login_endpoint_maps_unverified_and_throttled(auth_config, monkeypatch):
    service, users, sessions = make_service(verified=False)
    app.state.auth_service = service
    app.state.user_repository = users
    app.state.auth_sessions = sessions
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT", 1)
    with TestClient(app) as client:
        unverified = client.post("/api/v1/auth/login", json={
            "email": "user@example.com", "password": PASSWORD,
        })
    assert unverified.status_code == 403
    assert unverified.json() == {"detail": {"code": "EMAIL_NOT_VERIFIED"}}

    service, users, sessions = make_service()
    app.state.auth_service = service
    app.state.user_repository = users
    app.state.auth_sessions = sessions
    with TestClient(app) as client:
        first = client.post("/api/v1/auth/login", json={
            "email": "user@example.com", "password": "WrongPassword!12345",
        })
        second = client.post("/api/v1/auth/login", json={
            "email": "user@example.com", "password": PASSWORD,
        })
    assert first.status_code == 401
    assert second.status_code == 429


def test_unverified_account_is_rejected_after_correct_password(auth_config):
    service, _, _ = make_service(verified=False)
    with pytest.raises(EmailNotVerified):
        service.login("user@example.com", PASSWORD, "127.0.0.1")


def test_login_throttles_account_and_ip(auth_config, monkeypatch):
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT", 1)
    service, _, _ = make_service()
    with pytest.raises(InvalidCredentials):
        service.login("user@example.com", "WrongPassword!12345", "127.0.0.1")
    with pytest.raises(RateLimitExceeded):
        service.login("user@example.com", PASSWORD, "127.0.0.1")


def test_refresh_rotates_tokens_and_keeps_original_deadline(auth_config):
    service, _, sessions = make_service()
    login = service.login("user@example.com", PASSWORD, "127.0.0.1")
    session = next(iter(sessions.rows.values()))
    original_deadline = session["session_expires_at"]
    assert 86390 <= (original_deadline - datetime.now(timezone.utc)).total_seconds() <= 86400

    refreshed = service.refresh(login["refresh_token"])
    rotated = sessions.rows[session["_id"]]
    assert refreshed["refresh_token"] != login["refresh_token"]
    assert rotated["session_expires_at"] == original_deadline
    assert rotated["access_expires_at"] <= original_deadline
    assert rotated["refresh_token_hash"] == hash_token(refreshed["refresh_token"])


def test_refresh_caps_access_expiry_at_fixed_session_deadline(auth_config):
    service, _, sessions = make_service()
    login = service.login("user@example.com", PASSWORD, "127.0.0.1")
    session = next(iter(sessions.rows.values()))
    deadline = datetime.now(timezone.utc) + timedelta(seconds=5)
    session["session_expires_at"] = deadline

    refreshed = service.refresh(login["refresh_token"])
    rotated = sessions.rows[session["_id"]]
    assert rotated["session_expires_at"] == deadline
    assert rotated["access_expires_at"] <= deadline
    assert refreshed["expires_in"] <= 5


def test_expired_refresh_token_is_rejected(auth_config):
    service, _, sessions = make_service()
    login = service.login("user@example.com", PASSWORD, "127.0.0.1")
    session = next(iter(sessions.rows.values()))
    session["session_expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    with pytest.raises(InvalidRefreshToken):
        service.refresh(login["refresh_token"])


def test_reuse_of_rotated_refresh_token_revokes_session(auth_config):
    service, _, sessions = make_service()
    initial = service.login("user@example.com", PASSWORD, "127.0.0.1")
    rotated = service.refresh(initial["refresh_token"])

    with pytest.raises(InvalidRefreshToken):
        service.refresh(initial["refresh_token"])
    session = next(iter(sessions.rows.values()))
    assert session["revoked"] is True
    assert sessions.find_active_by_access_hash(hash_token(rotated["access_token"]),
                                               datetime.now(timezone.utc)) is None


def test_concurrent_refresh_cannot_rotate_same_token_twice(auth_config):
    service, _, sessions = make_service(sessions=BarrierSessions())
    initial = service.login("user@example.com", PASSWORD, "127.0.0.1")

    def refresh():
        try:
            return service.refresh(initial["refresh_token"])
        except InvalidRefreshToken:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: refresh(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert next(iter(sessions.rows.values()))["revoked"] is True


def test_me_requires_active_bearer_and_returns_safe_profile(auth_config):
    service, users, sessions = make_service()
    tokens = service.login("user@example.com", PASSWORD, "127.0.0.1")
    app.state.auth_service = service
    app.state.auth_sessions = sessions
    app.state.user_repository = users

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
    assert response.status_code == 200
    assert response.json() == {
        "id": "user-1", "name": "Test User", "email": "user@example.com",
        "role": "user", "email_verified": True,
    }
    assert "password_hash" not in response.text


def test_me_returns_distinct_code_for_expired_access_in_active_session(auth_config):
    service, users, sessions = make_service()
    tokens = service.login("user@example.com", PASSWORD, "127.0.0.1")
    session = next(iter(sessions.rows.values()))
    session["access_expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    app.state.auth_service = service
    app.state.auth_sessions = sessions
    app.state.user_repository = users

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "ACCESS_TOKEN_EXPIRED"


def test_logout_revokes_access_and_refresh_tokens(auth_config):
    service, users, sessions = make_service()
    tokens = service.login("user@example.com", PASSWORD, "127.0.0.1")
    app.state.auth_service = service
    app.state.auth_sessions = sessions
    app.state.user_repository = users

    with TestClient(app) as client:
        logout = client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
        after_logout = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
    assert logout.status_code == 204
    assert after_logout.status_code == 401
    with pytest.raises(InvalidRefreshToken):
        service.refresh(tokens["refresh_token"])


def test_login_me_refresh_logout_swagger_flow(auth_config):
    service, users, sessions = make_service()
    app.state.auth_service = service
    app.state.auth_sessions = sessions
    app.state.user_repository = users
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={
            "email": "user@example.com", "password": PASSWORD,
        })
        first_tokens = login.json()
        me_before = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {first_tokens['access_token']}"
        })
        refresh = client.post("/api/v1/auth/refresh", json={
            "refresh_token": first_tokens["refresh_token"],
        })
        second_tokens = refresh.json()
        old_access = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {first_tokens['access_token']}"
        })
        me_after = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {second_tokens['access_token']}"
        })
        logout = client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {second_tokens['access_token']}"
        })
        revoked_refresh = client.post("/api/v1/auth/refresh", json={
            "refresh_token": second_tokens["refresh_token"],
        })
    assert login.status_code == refresh.status_code == 200
    assert me_before.status_code == me_after.status_code == 200
    assert old_access.status_code == 401
    assert logout.status_code == 204
    assert revoked_refresh.status_code == 401
