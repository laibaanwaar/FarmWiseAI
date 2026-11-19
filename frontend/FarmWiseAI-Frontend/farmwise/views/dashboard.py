"""Farmer dashboard - welcome, ask box, recent questions, saved answers."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.data import RECENT_QUESTIONS, SAVED
from farmwise.routes import go, href


def _start_question(question: str, crop_key: str) -> None:
    from farmwise.views import chat

    chat.seed(question, crop_key)


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
                _start_question(question.strip(), st.session_state.chat_crop)
                go("chat")

        st.write("")
        left, right = st.columns([1.15, 1], gap="large")

        with left:
            rows = "".join(
                f"""
<a class="fw-qrow" href="{href('chat', q=r['q'])}">
  <span class="fw-ico" style="display:inline-flex">{T.icon('send')}</span>
  <span class="fw-qtext">{r['q']}</span>
  <span class="fw-chip">{T.icon('leaf')}{r['crop']}</span>
  <span class="fw-ico" style="display:inline-flex">{T.icon('arrow')}</span>
</a>"""
                for r in RECENT_QUESTIONS
            )
            T.show(
                f"""
<div class="fw-row-between" style="margin-bottom:12px">
  <h3 class="fw-h3">Recent Questions</h3>
  <a class="fw-small" href="{href('saved')}" style="font-weight:600;color:var(--text)">View All &rsaquo;</a>
</div>
<div class="fw-tablecard">{rows}</div>
""",
                unsafe_allow_html=True,
            )

        with right:
            cards = "".join(
                f"""
<a class="fw-card" href="{href('saved')}" style="text-decoration:none">
  <div class="fw-card-media" style="{T.media(s['image'], 0, 0.12)};height:130px"></div>
  <div class="fw-card-body" style="padding:16px 16px 18px">
    <span class="fw-chip">{T.icon('leaf')}{s['crop']}</span>
    <div class="fw-h4">{s['title']}</div>
    <p class="fw-small">{s['blurb']}</p>
  </div>
</a>"""
                for s in SAVED[:2]
            )
            T.show(
                f"""
<div class="fw-row-between" style="margin-bottom:12px">
  <h3 class="fw-h3">Saved Answers</h3>
  <a class="fw-small" href="{href('saved')}" style="font-weight:600;color:var(--text)">View all &rsaquo;</a>
</div>
<div class="fw-grid grid-2">{cards}</div>
""",
                unsafe_allow_html=True,
            )
