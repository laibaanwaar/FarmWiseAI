"""Services page - practical help broken down by farming problem."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.data import SERVICES


def render() -> None:
    ui.top_nav("services")

    ui.hero(
        "Practical help<br>for your crops.",
        "Handbook-based answers for crop care, pest and disease management, and best practices.",
    )

    cards = "".join(
        ui.service_card(s["icon"], s["title"], s["text"], s["image"]) for s in SERVICES
    )
    T.show(
        f'<section class="fw-section"><div class="fw-grid grid-3">{cards}</div></section>',
        unsafe_allow_html=True,
    )

    T.show(
        f"""
<section class="fw-section dark" style="position:relative;isolation:isolate">
  <div style="position:absolute;inset:0;z-index:-1;opacity:.35;{T.media('wheat_close', 0.2, 0.6)}"></div>
  <div class="fw-row-between">
    <div>
      <h2 class="fw-h2" style="margin:0">Ask, get a trusted answer,<br>with the source.</h2>
      <p class="fw-sub" style="margin-top:12px">
        Clear, handbook-based guidance for your crops, anytime.
      </p>
    </div>
    <a class="fw-btn fw-btn-lime" href="/chat">Ask a crop question {T.icon("arrow")}</a>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )
    ui.footer()
