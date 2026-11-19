"""Session state bootstrap shared by the operator + admin pages."""

from __future__ import annotations

import streamlit as st

from farmwise import data


def init() -> None:
    ss = st.session_state
    ss.setdefault("users", [dict(u) for u in data.USERS])
    ss.setdefault("audit", [dict(a) for a in data.AUDIT])
    ss.setdefault("account", None)
    ss.setdefault("pending_email", "farmer@example.com")
    ss.setdefault("chat_messages", [])
    ss.setdefault("chat_crop", "cotton")
    ss.setdefault("chat_lang", "en")
    ss.setdefault("chat_title", "Fusarium wilt in cotton")
    ss.setdefault("last_answer", None)
    ss.setdefault("theme_crop", "cotton")


def log(action: str, details: str, actor: str = "Admin") -> None:
    st.session_state.audit.insert(
        0,
        {"time": "Just now", "actor": actor, "action": action, "details": details},
    )
