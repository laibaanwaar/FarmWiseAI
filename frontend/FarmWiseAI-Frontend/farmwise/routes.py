"""URL paths + slug based navigation helpers (no heavy imports, so every module
can use it without creating import cycles)."""

from __future__ import annotations

from urllib.parse import urlencode

PATHS = {
    "home": "home",
    "about": "about",
    "services": "services",
    "crops": "crops",
    "signup": "signup",
    "verify": "verify-email",
    "resend": "resend-code",
    "login": "login",
    "account": "account",
    "forgot": "forgot-password",
    "reset": "reset-password",
    "dashboard": "app",
    "chat": "chat",
    "saved": "saved-answers",
    "admin": "admin",
    "admin_users": "admin-users",
    "admin_audit": "admin-audit",
    "admin_settings": "admin-settings",
}


def href(slug: str, **params) -> str:
    """Absolute in-app URL for a page slug, optionally with query params."""
    url = "/" if slug == "home" else "/" + PATHS[slug]
    if params:
        url += "?" + urlencode({k: v for k, v in params.items() if v is not None})
    return url


def go(slug: str, **params) -> None:
    """Client side navigation that keeps the current session (chat history etc.)."""
    import streamlit as st

    from farmwise.pages import registry

    target = registry()[slug]
    if params:
        st.session_state["_nav_params"] = params
    st.switch_page(target)
