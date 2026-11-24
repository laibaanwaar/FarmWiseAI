"""Session state bootstrap shared by the operator + admin pages."""

from __future__ import annotations

import streamlit as st

from farmwise import data


def init() -> None:
    ss = st.session_state
    ss.setdefault("users", [dict(u) for u in data.USERS])
    ss.setdefault("audit", [dict(a) for a in data.AUDIT])
    ss.setdefault("account", None)
    ss.setdefault("auth_access_token", None)
    ss.setdefault("auth_refresh_token", None)
    ss.setdefault("auth_expires_in", None)
    ss.setdefault("auth_user", None)
    ss.setdefault("pending_email", "")
    if ss.get("pending_email") == "farmer@example.com" and ss.get("account") is None:
        # Migrate the old demo fallback so it cannot be treated as a real pending signup.
        ss["pending_email"] = ""
    ss.setdefault("chat_messages", [])
    ss.setdefault("chat_active_conversation", None)
    ss.setdefault("chat_history", [])
    ss.setdefault("chat_history_loaded", False)
    ss.setdefault("chat_owner_id", None)
    ss.setdefault("chat_request_inflight", False)
    ss.setdefault("theme_crop", "cotton")


def log(action: str, details: str, actor: str = "Admin") -> None:
    st.session_state.audit.insert(
        0,
        {"time": "Just now", "actor": actor, "action": action, "details": details},
    )
