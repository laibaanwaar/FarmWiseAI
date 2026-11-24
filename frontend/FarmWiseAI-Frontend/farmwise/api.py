"""HTTP client for the FarmWiseAI backend API."""

import os

import requests


API_BASE_URL = os.getenv(
    "FARMWISE_API_URL",
    "http://127.0.0.1:8000/api/v1",
).rstrip("/")


class APIError(Exception):
    """Readable error returned by the backend or connection."""


def api_request(method: str, path: str, token: str | None = None, payload: dict | None = None):
    url = f"{API_BASE_URL}/{path.lstrip('/')}"
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise APIError(
            "Backend se connection nahi ho saka. Check karo ke backend running hai."
        ) from exc

    if response.status_code == 204:
        return None

    try:
        data = response.json()
    except ValueError:
        data = {}

    if not response.ok:
        detail = data.get("detail", "Request failed.") if isinstance(data, dict) else "Request failed."

        if isinstance(detail, dict):
            detail = detail.get("message", "Request failed.")

        raise APIError(str(detail))

    return data
