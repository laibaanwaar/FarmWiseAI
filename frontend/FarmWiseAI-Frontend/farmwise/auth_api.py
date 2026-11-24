"""Auth endpoint wrappers using the shared uncached API client."""

from __future__ import annotations

from typing import Any, MutableMapping

from farmwise.api_client import (
    APIError,
    get_json,
    post_authenticated,
    post_json,
)


def signup(name: str, email: str, password: str) -> dict[str, Any]:
    return post_json("/api/v1/auth/signup", {
        "name": name,
        "email": email,
        "password": password,
    })


def verify_email(email: str, otp: str) -> dict[str, Any]:
    return post_json("/api/v1/auth/verify-email", {
        "email": email,
        "otp": otp,
    })


def resend_verification(email: str) -> dict[str, Any]:
    return post_json("/api/v1/auth/resend-verification", {
        "email": email,
    })


def _validate_tokens(payload: dict[str, Any]) -> dict[str, Any]:
    access = payload.get("access_token")
    refresh = payload.get("refresh_token")
    token_type = payload.get("token_type")
    expires_in = payload.get("expires_in")
    if (not isinstance(access, str) or not access.strip()
            or not isinstance(refresh, str) or not refresh.strip()
            or not isinstance(token_type, str) or token_type.casefold() != "bearer"
            or isinstance(expires_in, bool) or not isinstance(expires_in, int)
            or expires_in <= 0):
        raise APIError("The login service returned an invalid token response.", retryable=True)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


def login(email: str, password: str) -> dict[str, Any]:
    return _validate_tokens(post_json("/api/v1/auth/login", {
        "email": email,
        "password": password,
    }))


def _validate_profile(payload: dict[str, Any]) -> dict[str, Any]:
    profile = {
        "id": payload.get("id"),
        "name": payload.get("name"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "email_verified": payload.get("email_verified"),
    }
    if (any(not isinstance(profile[key], str) or not profile[key].strip()
            for key in ("id", "name", "email", "role"))
            or not isinstance(profile["email_verified"], bool)):
        raise APIError("The profile service returned an invalid user profile.", retryable=True)
    return profile


def _set_profile(session_state: MutableMapping[str, Any], profile: dict[str, Any]) -> None:
    session_state["auth_user"] = profile
    # Keep the existing app navigation compatibility field profile-only.
    session_state["account"] = {
        "name": profile["name"],
        "email": profile["email"],
    }


def clear_user_data(session_state: MutableMapping[str, Any]) -> None:
    session_state["chat_messages"] = []
    session_state["chat_active_conversation"] = None
    session_state["chat_history"] = []
    session_state["chat_history_loaded"] = False
    session_state["chat_history_error"] = None
    session_state["chat_query_error"] = None
    session_state["chat_notice"] = None
    session_state["chat_owner_id"] = None
    session_state["chat_request_inflight"] = False
    session_state.pop("chat_pending_question", None)
    session_state.pop("_chat_route_question", None)
    session_state["chat_crop"] = None
    session_state["chat_lang"] = None
    session_state["chat_title"] = "New chat"
    session_state["last_answer"] = None
    session_state["theme_crop"] = "cotton"
    session_state.pop("_nav_params", None)


def clear_auth_state(session_state: MutableMapping[str, Any]) -> None:
    for key in (
        "auth_access_token", "auth_refresh_token", "auth_expires_in",
        "auth_user", "account", "auth_refresh_inflight", "pending_email",
        "auth_pending_login_email",
        "otp_notice", "signup_notice", "auth_notice",
        *(f"otp_{index}" for index in range(6)),
    ):
        session_state.pop(key, None)
    # Streamlit widget keys are cleared on the next login render, before widgets exist.
    session_state["clear_auth_widgets"] = True
    session_state["account"] = None
    clear_user_data(session_state)


def is_authenticated(session_state: MutableMapping[str, Any]) -> bool:
    return bool(session_state.get("auth_access_token") and session_state.get("auth_user"))


def can_access_private(session_state: MutableMapping[str, Any], *,
                       admin_only: bool = False) -> bool:
    if not is_authenticated(session_state):
        return False
    return not admin_only or session_state["auth_user"].get("role") == "admin"


def establish_session(email: str, password: str,
                      session_state: MutableMapping[str, Any]) -> dict[str, Any]:
    previous_email = (
        session_state.get("auth_user") or session_state.get("account") or {}
    ).get("email")
    previous_id = (session_state.get("auth_user") or {}).get("id")
    tokens = login(email, password)
    session_state["auth_access_token"] = tokens["access_token"]
    session_state["auth_refresh_token"] = tokens["refresh_token"]
    session_state["auth_expires_in"] = tokens["expires_in"]
    session_state["auth_pending_login_email"] = email
    try:
        profile = resume_login(session_state)
        if ((previous_email and previous_email.casefold() != profile["email"].casefold())
                or (previous_id and previous_id != profile["id"])):
            clear_user_data(session_state)
    except APIError as exc:
        if not exc.retryable:
            clear_auth_state(session_state)
        raise
    return profile


def resume_login(session_state: MutableMapping[str, Any]) -> dict[str, Any]:
    """Retry profile loading after a login succeeded but /me was temporarily unavailable."""
    expected_email = session_state.get("auth_pending_login_email")
    if not expected_email or not session_state.get("auth_access_token"):
        raise APIError("There is no pending login to resume.", status_code=401,
                       error_code="INVALID_ACCESS_TOKEN")
    profile = me(session_state)
    if profile["email"].casefold() != str(expected_email).strip().casefold():
        clear_auth_state(session_state)
        raise APIError("The profile email did not match the account used to log in.",
                       error_code="PROFILE_MISMATCH")
    session_state.pop("auth_pending_login_email", None)
    return profile


def _refresh(session_state: MutableMapping[str, Any]) -> None:
    refresh_token = session_state.get("auth_refresh_token")
    if not refresh_token:
        clear_auth_state(session_state)
        raise APIError("Your session has expired. Please log in again.",
                       status_code=401, error_code="SESSION_EXPIRED")
    if session_state.get("auth_refresh_inflight"):
        raise APIError("A session refresh is already in progress. Please retry.")

    session_state["auth_refresh_inflight"] = True
    try:
        try:
            tokens = _validate_tokens(post_json(
                "/api/v1/auth/refresh", {"refresh_token": refresh_token}
            ))
        except APIError as exc:
            if exc.status_code == 401:
                clear_auth_state(session_state)
                raise APIError("Your session has expired. Please log in again.",
                               status_code=401, error_code="SESSION_EXPIRED") from exc
            raise
        # Set both rotated tokens together only after the full response validates.
        session_state.update({
            "auth_access_token": tokens["access_token"],
            "auth_refresh_token": tokens["refresh_token"],
            "auth_expires_in": tokens["expires_in"],
        })
    finally:
        session_state.pop("auth_refresh_inflight", None)


def _authenticated_request(session_state: MutableMapping[str, Any], method: str,
                           path: str, *, allow_empty: bool = False,
                           payload: dict[str, Any] | None = None,
                           params: dict[str, Any] | None = None,
                           timeout: tuple[float, float] | float = (3.05, 15)) -> dict[str, Any]:
    access_token = session_state.get("auth_access_token")
    if not access_token:
        raise APIError("Please log in to continue.", status_code=401,
                       error_code="INVALID_ACCESS_TOKEN")
    default_timeout = timeout == (3.05, 15)
    try:
        if method == "GET":
            if params is None and default_timeout:
                return get_json(path, access_token=access_token)
            return get_json(path, access_token=access_token, params=params, timeout=timeout)
        if payload is None and default_timeout and not allow_empty:
            return post_authenticated(path, access_token=access_token)
        if payload is None and default_timeout and allow_empty:
            return post_authenticated(path, access_token=access_token, allow_empty=True)
        return post_authenticated(path, access_token=access_token,
                                  payload=payload, allow_empty=allow_empty, timeout=timeout)
    except APIError as exc:
        if exc.error_code == "ACCESS_TOKEN_EXPIRED":
            _refresh(session_state)
            # Exactly one retry; the second 401 is definitive and never refreshes again.
            new_token = session_state.get("auth_access_token")
            try:
                if method == "GET":
                    if params is None and default_timeout:
                        return get_json(path, access_token=new_token)
                    return get_json(path, access_token=new_token, params=params, timeout=timeout)
                if payload is None and default_timeout and not allow_empty:
                    return post_authenticated(path, access_token=new_token)
                if payload is None and default_timeout and allow_empty:
                    return post_authenticated(path, access_token=new_token, allow_empty=True)
                return post_authenticated(path, access_token=new_token,
                                          payload=payload, allow_empty=allow_empty,
                                          timeout=timeout)
            except APIError as retry_error:
                if retry_error.status_code == 401:
                    clear_auth_state(session_state)
                    raise APIError("Your session has expired. Please log in again.",
                                   status_code=401, error_code="SESSION_EXPIRED") from retry_error
                raise
        if exc.status_code == 401:
            clear_auth_state(session_state)
        raise


def authenticated_request(session_state: MutableMapping[str, Any], method: str,
                          path: str, *, payload: dict[str, Any] | None = None,
                          params: dict[str, Any] | None = None,
                          timeout: tuple[float, float] | float = (3.05, 15)) -> dict[str, Any]:
    """Authenticated request using the same one-time expired-token refresh path."""
    return _authenticated_request(session_state, method, path, payload=payload,
                                  params=params, timeout=timeout)


def me(session_state: MutableMapping[str, Any]) -> dict[str, Any]:
    profile = _validate_profile(_authenticated_request(
        session_state, "GET", "/api/v1/auth/me"
    ))
    previous_email = (session_state.get("auth_user") or {}).get("email")
    previous_id = (session_state.get("auth_user") or {}).get("id")
    if ((previous_email and previous_email.casefold() != profile["email"].casefold())
            or (previous_id and previous_id != profile["id"])):
        clear_user_data(session_state)
    _set_profile(session_state, profile)
    return profile


def logout(session_state: MutableMapping[str, Any]) -> None:
    _authenticated_request(
        session_state, "POST", "/api/v1/auth/logout", allow_empty=True
    )


def logout_session(session_state: MutableMapping[str, Any]) -> None:
    try:
        logout(session_state)
    except APIError:
        # Definitive expiry/revocation clears auth in _authenticated_request.
        # Network and server failures leave it intact and must be retried.
        if not session_state.get("auth_access_token"):
            clear_auth_state(session_state)
            return
        raise
    clear_auth_state(session_state)
