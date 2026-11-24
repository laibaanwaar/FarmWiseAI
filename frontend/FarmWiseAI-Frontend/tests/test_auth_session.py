from __future__ import annotations

import unittest
from unittest.mock import patch

from farmwise import auth_api
from farmwise.api_client import APIError


TOKENS = {
    "access_token": "access-a",
    "refresh_token": "refresh-a",
    "token_type": "bearer",
    "expires_in": 900,
}
PROFILE = {
    "id": "user-a",
    "name": "Test User",
    "email": "user@example.com",
    "role": "user",
    "email_verified": True,
}


class AuthSessionTests(unittest.TestCase):
    def test_successful_login_loads_profile(self):
        def login_request(path, payload):
            self.assertEqual(path, "/api/v1/auth/login")
            self.assertEqual(payload, {
                "email": "user@example.com",
                "password": " Secret password! ",
            })
            return TOKENS

        def profile_request(path, *, access_token):
            self.assertEqual(path, "/api/v1/auth/me")
            self.assertEqual(access_token, "access-a")
            return PROFILE

        with patch.object(auth_api, "post_json", side_effect=login_request), patch.object(
            auth_api, "get_json", side_effect=profile_request
        ):
            state = {}
            profile = auth_api.establish_session(
                "user@example.com", " Secret password! ", state
            )

        self.assertEqual(profile, PROFILE)
        self.assertEqual(state["auth_access_token"], "access-a")
        self.assertEqual(state["auth_refresh_token"], "refresh-a")
        self.assertEqual(state["auth_user"], PROFILE)
        self.assertEqual(state["account"], {"name": "Test User", "email": "user@example.com"})
        self.assertFalse(any("password" in key for key in state))

    def test_wrong_password_and_unverified_email_do_not_authenticate(self):
        for error in (
            APIError("Invalid email or password.", status_code=401),
            APIError("Email not verified.", status_code=403, error_code="EMAIL_NOT_VERIFIED"),
        ):
            with self.subTest(error=error.error_code or error.status_code):
                state = {}
                with patch.object(auth_api, "post_json", side_effect=error):
                    with self.assertRaises(APIError):
                        auth_api.establish_session("user@example.com", "wrong", state)
                self.assertFalse(auth_api.is_authenticated(state))
                self.assertNotIn("auth_access_token", state)

    def test_expired_access_refreshes_once_and_retries_me(self):
        state = {
            "auth_access_token": "old-access",
            "auth_refresh_token": "old-refresh",
            "auth_user": PROFILE,
            "chat_messages": ["keep this"],
        }
        rotated = {**TOKENS, "access_token": "new-access", "refresh_token": "new-refresh"}
        calls = {"me": 0, "refresh": 0}

        def get_json(path, *, access_token):
            calls["me"] += 1
            if access_token == "old-access":
                raise APIError("Expired", status_code=401, error_code="ACCESS_TOKEN_EXPIRED")
            self.assertEqual(access_token, "new-access")
            return PROFILE

        def post_json(path, payload):
            calls["refresh"] += 1
            self.assertEqual(path, "/api/v1/auth/refresh")
            self.assertEqual(payload, {"refresh_token": "old-refresh"})
            return rotated

        with patch.object(auth_api, "get_json", side_effect=get_json), patch.object(
            auth_api, "post_json", side_effect=post_json
        ):
            self.assertEqual(auth_api.me(state), PROFILE)

        self.assertEqual(calls, {"me": 2, "refresh": 1})
        self.assertEqual(state["auth_access_token"], "new-access")
        self.assertEqual(state["auth_refresh_token"], "new-refresh")
        self.assertEqual(state["chat_messages"], ["keep this"])

    def test_refresh_server_failure_preserves_session(self):
        state = {
            "auth_access_token": "old-access",
            "auth_refresh_token": "old-refresh",
            "auth_user": PROFILE,
            "account": {"name": PROFILE["name"], "email": PROFILE["email"]},
            "chat_messages": ["keep this"],
        }
        expired = APIError("Expired", status_code=401, error_code="ACCESS_TOKEN_EXPIRED")
        unavailable = APIError("Service unavailable", status_code=503)
        with patch.object(auth_api, "get_json", side_effect=expired), patch.object(
            auth_api, "post_json", side_effect=unavailable
        ):
            with self.assertRaisesRegex(APIError, "Service unavailable"):
                auth_api.me(state)

        self.assertEqual(state["auth_access_token"], "old-access")
        self.assertEqual(state["auth_refresh_token"], "old-refresh")
        self.assertEqual(state["auth_user"], PROFILE)
        self.assertEqual(state["chat_messages"], ["keep this"])
        self.assertNotIn("auth_refresh_inflight", state)

    def test_definitive_refresh_failure_clears_authentication(self):
        state = {
            "auth_access_token": "old-access",
            "auth_refresh_token": "old-refresh",
            "auth_user": PROFILE,
            "account": {"name": PROFILE["name"], "email": PROFILE["email"]},
        }
        expired_access = APIError("Expired", status_code=401, error_code="ACCESS_TOKEN_EXPIRED")
        expired_refresh = APIError("Invalid or expired refresh token.", status_code=401)
        with patch.object(auth_api, "get_json", side_effect=expired_access), patch.object(
            auth_api, "post_json", side_effect=expired_refresh
        ):
            with self.assertRaisesRegex(APIError, "session has expired"):
                auth_api.me(state)
        self.assertFalse(auth_api.is_authenticated(state))
        self.assertIsNone(state["account"])

    def test_backend_unavailable_does_not_create_session(self):
        unavailable = APIError("Could not connect", status_code=None)
        with patch.object(auth_api, "post_json", side_effect=unavailable):
            state = {}
            with self.assertRaisesRegex(APIError, "Could not connect"):
                auth_api.establish_session("user@example.com", "password", state)
        self.assertFalse(auth_api.is_authenticated(state))

    def test_temporary_profile_failure_keeps_login_resumable(self):
        state = {}
        first = {"count": 0}

        def get_json(path, *, access_token):
            first["count"] += 1
            if first["count"] == 1:
                raise APIError("Service unavailable", status_code=503, retryable=True)
            return PROFILE

        with patch.object(auth_api, "post_json", return_value=TOKENS), patch.object(
            auth_api, "get_json", side_effect=get_json
        ):
            with self.assertRaisesRegex(APIError, "Service unavailable"):
                auth_api.establish_session("user@example.com", "password", state)
            self.assertEqual(state["auth_access_token"], "access-a")
            self.assertEqual(state["auth_pending_login_email"], "user@example.com")
            self.assertFalse(auth_api.is_authenticated(state))
            self.assertEqual(auth_api.resume_login(state), PROFILE)

        self.assertTrue(auth_api.is_authenticated(state))
        self.assertNotIn("auth_pending_login_email", state)

    def test_account_change_clears_previous_chat_data(self):
        other = {**PROFILE, "email": "other@example.com", "id": "other"}
        state = {
            "account": {"name": "Previous user", "email": "previous@example.com"},
            "chat_messages": ["previous user's private chat"],
            "last_answer": {"private": True},
        }
        with patch.object(auth_api, "post_json", return_value=TOKENS), patch.object(
            auth_api, "get_json", return_value=other
        ):
            auth_api.establish_session("other@example.com", "secret", state)
        self.assertEqual(state["auth_user"], other)
        self.assertEqual(state["chat_messages"], [])
        self.assertIsNone(state["last_answer"])

    def test_logout_clears_auth_and_private_user_data(self):
        state = {
            "auth_access_token": "access-a",
            "auth_refresh_token": "refresh-a",
            "auth_user": PROFILE,
            "account": {"name": PROFILE["name"], "email": PROFILE["email"]},
            "chat_messages": ["private chat"],
            "last_answer": {"private": True},
        }
        with patch.object(auth_api, "post_authenticated", return_value={}) as logout_call:
            auth_api.logout_session(state)

        logout_call.assert_called_once_with(
            "/api/v1/auth/logout", access_token="access-a", allow_empty=True
        )
        self.assertFalse(auth_api.is_authenticated(state))
        self.assertIsNone(state["account"])
        self.assertEqual(state["chat_messages"], [])
        self.assertIsNone(state["last_answer"])

    def test_private_page_access_requires_auth_and_admin_role(self):
        self.assertFalse(auth_api.can_access_private({}))
        regular_user = {"auth_access_token": "token", "auth_user": PROFILE}
        self.assertTrue(auth_api.can_access_private(regular_user))
        self.assertFalse(auth_api.can_access_private(regular_user, admin_only=True))
        admin_user = {"auth_access_token": "token", "auth_user": {**PROFILE, "role": "admin"}}
        self.assertTrue(auth_api.can_access_private(admin_user, admin_only=True))

    def test_two_sessions_keep_profiles_and_tokens_isolated(self):
        first = {**PROFILE, "email": "first@example.com", "id": "first"}
        second = {**PROFILE, "email": "second@example.com", "id": "second"}
        states = [
            {"auth_access_token": "token-first", "auth_refresh_token": "refresh-first"},
            {"auth_access_token": "token-second", "auth_refresh_token": "refresh-second"},
        ]
        profiles = {"token-first": first, "token-second": second}
        with patch.object(auth_api, "get_json", side_effect=lambda path, *, access_token: profiles[access_token]):
            self.assertEqual(auth_api.me(states[0]), first)
            self.assertEqual(auth_api.me(states[1]), second)

        self.assertEqual(states[0]["auth_user"]["email"], "first@example.com")
        self.assertEqual(states[1]["auth_user"]["email"], "second@example.com")
        self.assertEqual(states[0]["auth_refresh_token"], "refresh-first")
        self.assertEqual(states[1]["auth_refresh_token"], "refresh-second")


if __name__ == "__main__":
    unittest.main()
