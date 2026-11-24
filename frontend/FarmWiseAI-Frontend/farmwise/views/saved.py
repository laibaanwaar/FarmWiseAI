"""Conversation history shown in the existing Saved Answers navigation view."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.views.chat import history_panel


def render() -> None:
    with st.container(key="appframe"):
        ui.app_nav("saved")
        T.show(
            """
<h1 class="fw-admin-title">Saved Answers</h1>
<p class="fw-admin-sub">Browse your stored conversations and their source citations.</p>
""",
            unsafe_allow_html=True,
        )
        with st.container(key="saved_conversation_history"):
            history_panel("Your conversations", load_messages_inline=True)
