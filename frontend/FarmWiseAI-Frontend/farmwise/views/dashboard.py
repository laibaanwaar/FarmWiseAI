"""Farmer dashboard - welcome, ask box, recent questions, saved answers."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.routes import go


def render() -> None:
    with st.container(key="appframe"):
        ui.app_nav("dashboard")

        T.show(f"<style>.st-key-apphero{{{T.media('farmer', 0.1, 0.45, 'center 26%')}}}</style>", unsafe_allow_html=True)
        with st.container(key="apphero"):
            T.show(
                """
<div style="max-width:430px">
  <h2 style="color:#fff;font-size:34px;font-weight:800;letter-spacing:-.03em;line-height:1.08;margin:0 0 10px">
    Welcome to<br>FarmWiseAI
  </h2>
  <p style="color:rgba(255,255,255,.85);font-size:14.5px;margin:0 0 16px;max-width:40ch">
    AI answers for healthier crops and higher yields.
  </p>
</div>
""",
                unsafe_allow_html=True,
            )
            with st.form("dash_ask", border=False, clear_on_submit=True):
                cols = st.columns([4.4, 1], gap="small", vertical_alignment="bottom")
                question = cols[0].text_input(
                    "Ask a crop question",
                    placeholder="Ask a crop question",
                    label_visibility="collapsed",
                    key="dash_question",
                )
                asked = cols[1].form_submit_button("Ask", type="primary", width="stretch")
            if asked and question.strip():
                from farmwise.views import chat

                chat.new_chat()
                st.session_state["chat_pending_question"] = question.strip()
                go("chat")

        st.write("")
        left, right = st.columns([1.15, 1], gap="large")

        with left:
            from farmwise.views import chat

            with st.container(key="dashboard_history"):
                chat.history_panel("Your conversations", open_chat=True)

        with right:
            T.show(
                """
<div class="fw-row-between" style="margin-bottom:12px">
  <h3 class="fw-h3">Continue chatting</h3>
</div>
<div class="fw-tablecard" style="padding:18px">
  <p class="fw-small">Your answers and citations are saved in your conversation history.</p>
</div>
""",
                unsafe_allow_html=True,
            )
