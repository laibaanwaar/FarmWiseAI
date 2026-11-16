import threading
import time
from datetime import datetime, timedelta, timezone

from backend.core import config
from backend.core.security import (
    hash_otp, hash_password, hash_token, new_email_otp, new_opaque_token,
    verify_dummy_password, verify_password,
)


class RateLimiter:
    def __init__(self):
        self._events = {}
        self._lock = threading.Lock()

    def allow(self, scope, key, limit, window):
        now = time.monotonic()
        bucket = f"{scope}:{key}"
        with self._lock:
            recent = [stamp for stamp in self._events.get(bucket, []) if now - stamp < window]
            if len(recent) >= limit:
                self._events[bucket] = recent
                return False
            recent.append(now)
            self._events[bucket] = recent
            return True


class AuthService:
    def __init__(self, users, tokens, email_sender, sessions=None):
        self.users = users
        self.tokens = tokens
        self.email_sender = email_sender
        self.sessions = sessions
        self.limiter = RateLimiter()

    def _limited(self, scope, key, limit, window):
        if not self.limiter.allow(scope, key, limit, window):
            raise RateLimitExceeded

    def _deliver(self, user):
        otp = new_email_otp()
        self.tokens.delete_for_user(user["_id"])
        self.tokens.store(
            user["_id"], hash_otp(otp), config.EMAIL_OTP_TTL_SECONDS
        )
        try:
            self.email_sender(user["email"], otp)
        except Exception:
            # Delivery can be retried through resend-verification. Never log OTP or SMTP details.
            return False
        return True

    def signup(self, name, email, password, client_ip):
        self._limited("signup-ip", client_ip, config.SIGNUP_RATE_LIMIT,
                      config.SIGNUP_RATE_WINDOW_SECONDS)
        self._limited("signup-email", email, config.SIGNUP_RATE_LIMIT,
                      config.SIGNUP_RATE_WINDOW_SECONDS)
        password_hash = hash_password(password)
        user = self.users.create(name, email, password_hash)
        if user:
            self._deliver(user)
        return True

    def resend_verification(self, email, client_ip):
        self._limited("resend-ip", client_ip, config.RESEND_RATE_LIMIT,
                      config.RESEND_RATE_WINDOW_SECONDS)
        self._limited("resend-email", email, config.RESEND_RATE_LIMIT,
                      config.RESEND_RATE_WINDOW_SECONDS)
        user = self.users.find_pending_by_email(email)
        if user:
            self._deliver(user)
        return True

    def verify_email(self, email, otp, client_ip):
        self._limited("verify-ip", client_ip, config.VERIFY_RATE_LIMIT,
                      config.VERIFY_RATE_WINDOW_SECONDS)
        self._limited("verify-email", email, config.VERIFY_RATE_LIMIT,
                      config.VERIFY_RATE_WINDOW_SECONDS)
        user = self.users.find_pending_by_email(email)
        if not user:
            raise InvalidVerificationCode
        digest = hash_otp(otp)
        consumed = self.tokens.consume(digest, user["_id"])
        if not consumed or not self.users.mark_email_verified(user["_id"]):
            raise InvalidVerificationCode
        return True

    def login(self, email, password, client_ip):
        self._limited("login-ip", client_ip, config.LOGIN_RATE_LIMIT,
                      config.LOGIN_RATE_WINDOW_SECONDS)
        self._limited("login-account", email, config.LOGIN_RATE_LIMIT,
                      config.LOGIN_RATE_WINDOW_SECONDS)
        user = self.users.find_by_email(email)
        if not user:
            verify_dummy_password(password)
            raise InvalidCredentials
        if not verify_password(password, user.get("password_hash", "")):
            raise InvalidCredentials
        if not user.get("email_verified", False):
            raise EmailNotVerified
        if self.sessions is None:
            raise RuntimeError("Session repository is not configured.")

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(seconds=config.SESSION_TTL_SECONDS)
        access_expiry = min(
            now + timedelta(seconds=config.ACCESS_TOKEN_TTL_SECONDS), deadline
        )
        access_token, refresh_token = new_opaque_token(), new_opaque_token()
        self.sessions.create_session(
            user["_id"], hash_token(access_token), hash_token(refresh_token),
            access_expiry, deadline,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": max(0, int((access_expiry - now).total_seconds())),
        }

    def refresh(self, refresh_token):
        if self.sessions is None:
            raise RuntimeError("Session repository is not configured.")
        now = datetime.now(timezone.utc)
        old_hash = hash_token(refresh_token)
        session = self.sessions.find_active_by_refresh_hash(old_hash, now)
        if not session:
            self.sessions.revoke_if_reused_refresh_hash(old_hash, now)
            raise InvalidRefreshToken

        deadline = _as_utc(session["session_expires_at"])
        if deadline <= now:
            raise InvalidRefreshToken
        access_expiry = min(
            now + timedelta(seconds=config.ACCESS_TOKEN_TTL_SECONDS), deadline
        )
        access_token, next_refresh_token = new_opaque_token(), new_opaque_token()
        rotated = self.sessions.rotate_refresh(
            session["_id"], old_hash, hash_token(access_token),
            hash_token(next_refresh_token), access_expiry, now,
        )
        if not rotated:
            self.sessions.revoke_if_reused_refresh_hash(old_hash, now)
            raise InvalidRefreshToken
        return {
            "access_token": access_token,
            "refresh_token": next_refresh_token,
            "token_type": "bearer",
            "expires_in": max(0, int((access_expiry - now).total_seconds())),
        }

    def logout(self, session_id):
        if self.sessions is None:
            raise RuntimeError("Session repository is not configured.")
        return self.sessions.revoke(session_id, datetime.now(timezone.utc))


def _as_utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class RateLimitExceeded(Exception):
    pass


class InvalidVerificationCode(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class EmailNotVerified(Exception):
    pass


class InvalidRefreshToken(Exception):
    pass
