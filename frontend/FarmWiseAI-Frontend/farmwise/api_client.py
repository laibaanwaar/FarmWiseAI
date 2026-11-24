"""Small, uncached JSON client for calls from the Streamlit server."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests


class APIError(Exception):
    """Useful, safe-to-display details for an unsuccessful API request."""

    def __init__(self, message: str, *, status_code: int | None = None,
                 retry_after: str | None = None, error_code: str | None = None,
                 retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after
        self.error_code = error_code
        self.retryable = retryable


def _retry_after(response: requests.Response) -> str | None:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        seconds = max(0, int(value))
        return f"{seconds} seconds" if seconds != 1 else "1 second"
    except ValueError:
        try:
            deadline = parsedate_to_datetime(value)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            remaining = max(0, int((deadline - datetime.now(timezone.utc)).total_seconds()))
            return f"{remaining} seconds" if remaining != 1 else "1 second"
        except (TypeError, ValueError, OverflowError):
            return value


def _detail_message(detail: Any) -> str | None:
    if isinstance(detail, str):
        return detail.strip() or None
    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("msg")
        if isinstance(message, str) and message.strip():
            return message.strip()
        # Pydantic validation errors can identify fields as a list of loc parts.
        fields = detail.get("errors")
        if isinstance(fields, list):
            return _validation_message(fields)
    if isinstance(detail, list):
        return _validation_message(detail)
    return None


def _validation_message(errors: list[Any]) -> str | None:
    items: list[str] = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        location = error.get("loc") or error.get("field")
        if isinstance(location, (list, tuple)):
            field = ".".join(str(part) for part in location if part != "body")
        else:
            field = str(location or "")
        message = error.get("msg") or error.get("message")
        if isinstance(message, str) and message.strip():
            items.append(f"{field}: {message.strip()}" if field else message.strip())
    return "; ".join(items) or None


def request_json(method: str, path: str, *, payload: dict[str, Any] | None = None,
                 headers: dict[str, str] | None = None,
                 allow_empty: bool = False) -> dict[str, Any]:
    """Send JSON without caching or logging request contents."""
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)
        response = requests.request(
            method.upper(),
            f"{base_url}/{path.lstrip('/')}",
            json=payload,
            headers=request_headers,
            timeout=(3.05, 15),
        )
    except requests.Timeout as exc:
        raise APIError("The API request timed out. Please try again.", retryable=True) from exc
    except requests.ConnectionError as exc:
        raise APIError("Could not connect to the FarmWiseAI API. Check that it is running and try again.", retryable=True) from exc
    except requests.RequestException as exc:
        raise APIError("The API request could not be completed. Please try again.", retryable=True) from exc

    try:
        body = response.json()
    except requests.exceptions.JSONDecodeError:
        body = None

    if not response.ok:
        detail = body.get("detail") if isinstance(body, dict) else None
        error_code = detail.get("code") if isinstance(detail, dict) else None
        message = _detail_message(detail)
        if error_code == "EMAIL_NOT_VERIFIED":
            message = "Email not verified. Verify the address before logging in."
        elif error_code == "ACCOUNT_DISABLED":
            message = "This account is disabled. Contact support for help."
        if response.status_code == 422 and not message:
            message = "Some signup fields are invalid. Review the form and try again."
        elif response.status_code == 422 and message == "Invalid request.":
            message = "Invalid request. Review the submitted fields and backend validation requirements."
        elif response.status_code == 429 and not message:
            message = "Too many requests. Please wait before trying again."
        elif not message:
            message = f"The API returned an error (HTTP {response.status_code}). Please try again."
        raise APIError(message, status_code=response.status_code,
                       retry_after=_retry_after(response), error_code=error_code,
                       retryable=response.status_code == 429 or response.status_code >= 500)

    if response.status_code == 204 and allow_empty:
        return {}

    if body is None:
        raise APIError("The API returned a response that was not valid JSON.",
                       status_code=response.status_code, retryable=True)
    if not isinstance(body, dict):
        raise APIError("The API returned an unexpected response format.",
                       status_code=response.status_code, retryable=True)
    return body


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    return request_json("POST", path, payload=payload)


def get_json(path: str, *, access_token: str) -> dict[str, Any]:
    return request_json("GET", path, headers={"Authorization": f"Bearer {access_token}"})


def post_authenticated(path: str, *, access_token: str,
                       payload: dict[str, Any] | None = None,
                       allow_empty: bool = False) -> dict[str, Any]:
    return request_json(
        "POST", path, payload=payload,
        headers={"Authorization": f"Bearer {access_token}"},
        allow_empty=allow_empty,
    )
