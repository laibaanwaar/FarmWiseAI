import threading
import time

from backend.core import config
from backend.core.security import hash_password, hash_token, new_verification_token


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
    def __init__(self, users, tokens, email_sender):
        self.users = users
        self.tokens = tokens
        self.email_sender = email_sender
        self.limiter = RateLimiter()

    def _limited(self, scope, key, limit, window):
        if not self.limiter.allow(scope, key, limit, window):
            raise RateLimitExceeded

    def _deliver(self, user):
        token = new_verification_token()
        self.tokens.delete_for_user(user["_id"])
        self.tokens.store(
            user["_id"], hash_token(token), config.VERIFICATION_TOKEN_TTL_SECONDS
        )
        try:
            self.email_sender(user["email"], token)
        except Exception:
            # Delivery can be retried through resend-verification. Never log token or SMTP details.
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


class RateLimitExceeded(Exception):
    pass
