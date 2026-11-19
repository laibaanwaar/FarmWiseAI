"""Crops page - crop-specific entry points into the assistant."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.data import CROPS, QUESTIONS
from farmwise.routes import href

CARD_QUESTIONS = {
    "wheat": "When should I apply urea to wheat?",
    "rice": "How much water does rice need?",
    "cotton": "How can I control whitefly in cotton?",
}


def _crop_card(crop: dict) -> str:
    variant = "ghost" if crop["status"] == "Current demo" else "ghost"
    badge_icon = "bolt" if crop["status"] == "Current demo" else "calendar"
    target = href("chat", crop=crop["key"], q=CARD_QUESTIONS.get(crop["key"], crop["name"]))
    return f"""
<article class="fw-crop-card" style="{T.media(crop['image'], 0.05, 0.2)}">
  {ui.badge(crop["status"], variant, badge_icon)}
  <h3>{crop["name"]}</h3>
  <p>{crop["blurb"]}</p>
  <div><a class="fw-btn fw-btn-lime fw-btn-sm" href="{target}">{crop["cta"]} {T.icon("arrow")}</a></div>
</article>"""


def render() -> None:
    ui.top_nav("crops")

    ui.hero(
        "Explore your<br>crops",
        "Crop-specific guidance, best practices, and answers for Pakistan's key crops "
        "&mdash; starting with wheat, rice, and cotton.",
        cta=("Ask a crop question", "chat"),
    )

    T.show(
        '<section class="fw-section"><div class="fw-grid grid-3">'
        + "".join(_crop_card(c) for c in CROPS[:3])
        + "</div></section>",
        unsafe_allow_html=True,
    )

    pills = "".join(
        f'<a class="fw-pill-link" href="{href("chat", q=q)}">{q}</a>' for q in QUESTIONS
    )
    T.show(
        f"""
<section class="fw-section dark">
  <h2 class="fw-h2" style="margin-bottom:12px">Start with a crop question</h2>
  <p class="fw-sub" style="margin-bottom:26px">
    Get clear, practical answers for wheat, rice, and cotton from trusted, source-backed guidance.
  </p>
  <div class="fw-row" style="gap:14px">{pills}</div>
</section>
""",
        unsafe_allow_html=True,
    )

    T.show(
        f"""
<section class="fw-section cream">
  <div class="fw-split">
    <h2 class="fw-h2" style="margin:0">Focused<br>coverage for<br>Pakistan's<br>key crops.</h2>
    <p class="fw-sub fw-split-rule">
      We're building crop-by-crop coverage with practical, source-backed guidance
      tailored to Pakistan's conditions.
    </p>
  </div>
  <div style="margin-top:40px;height:250px;border-radius:18px;{T.media('wheat_close', 0, 0.15)}"></div>
</section>
""",
        unsafe_allow_html=True,
    )
    ui.footer()
