from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import requests

from farmwise.api_client import APIError, get_json, post_json


def response(status: int, payload=None, *, headers=None, raw: bytes | None = None):
    result = requests.Response()
    result.status_code = status
    result.headers.update(headers or {})
    result.url = "http://127.0.0.1:8000/test"
    result._content = raw if raw is not None else json.dumps(payload).encode("utf-8")
    return result


class APIClientTests(unittest.TestCase):
    def test_get_sends_bearer_token(self):
        with patch("farmwise.api_client.requests.request", return_value=response(200, {"id": "u1"})) as send:
            self.assertEqual(get_json("/api/v1/auth/me", access_token="secret-token"), {"id": "u1"})
        self.assertEqual(send.call_args.kwargs["headers"]["Authorization"], "Bearer secret-token")
        self.assertEqual(send.call_args.kwargs["timeout"], (3.05, 15))

    def test_validation_errors_include_field_details(self):
        body = {"detail": [{"loc": ["body", "email"], "msg": "invalid email"}]}
        with patch("farmwise.api_client.requests.request", return_value=response(422, body)):
            with self.assertRaises(APIError) as raised:
                post_json("/api/v1/auth/login", {"email": "bad", "password": "x"})
        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.message, "email: invalid email")

    def test_429_preserves_retry_after_and_backend_message(self):
        body = {"detail": "Too many login attempts. Try again later."}
        with patch(
            "farmwise.api_client.requests.request",
            return_value=response(429, body, headers={"Retry-After": "60"}),
        ):
            with self.assertRaises(APIError) as raised:
                post_json("/api/v1/auth/login", {"email": "a@b.com", "password": "x"})
        self.assertEqual(raised.exception.retry_after, "60 seconds")
        self.assertIn("Too many login attempts", raised.exception.message)

    def test_non_json_server_error_is_actionable(self):
        with patch(
            "farmwise.api_client.requests.request",
            return_value=response(503, raw=b"upstream unavailable"),
        ):
            with self.assertRaises(APIError) as raised:
                post_json("/api/v1/auth/login", {"email": "a@b.com", "password": "x"})
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("HTTP 503", raised.exception.message)

    def test_connection_and_timeout_failures_are_sanitized(self):
        for failure, expected in (
            (requests.Timeout("slow"), "timed out"),
            (requests.ConnectionError("unreachable"), "Could not connect"),
        ):
            with self.subTest(expected=expected), patch(
                "farmwise.api_client.requests.request", side_effect=failure
            ):
                with self.assertRaises(APIError) as raised:
                    post_json("/api/v1/auth/login", {"email": "a@b.com", "password": "secret"})
                self.assertIn(expected, raised.exception.message)
                self.assertNotIn("secret", raised.exception.message)


if __name__ == "__main__":
    unittest.main()
