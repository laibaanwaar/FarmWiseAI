"""About page - mission + 'every answer has a source'."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T


def render() -> None:
    ui.top_nav("about")

    ui.hero(
        "Built for the<br>people who<br>grow our food.",
        "FarmWiseAI helps farmers find practical answers in agricultural handbooks.",
        cta=("Try the assistant", "chat"),
    )

    ui.metrics(
        [
            ("5", "Crops covered"),
            ("10", "Handbook topics cited"),
            ("2", "Languages &mdash; English &amp; اردو"),
            ("100<span>%</span>", "Source-backed answers"),
        ]
    )

    T.show(
        f"""
<section class="fw-section">
  <div class="fw-split">
    <h2 class="fw-h2" style="margin:0">Our mission</h2>
    <p class="fw-sub fw-split-rule" style="max-width:44ch">
      To make trusted, source-backed agricultural knowledge practical and accessible
      for Pakistan's farmers, so they can take better care of their crops, increase
      yields, and manage risks with confidence.
    </p>
  </div>
  <div style="margin-top:36px;height:360px;border-radius:18px;{T.media('farmer', 0, 0.08, 'center 22%')}"></div>
</section>
""",
        unsafe_allow_html=True,
    )

    T.show(
        f"""
<section class="fw-section dark">
  <div class="fw-split" style="align-items:start">
    <div>
      <h2 class="fw-h2" style="margin-bottom:14px">Every answer<br>has a source.</h2>
      <p class="fw-sub">
        Our AI assistant doesn't guess. It gives clear, practical guidance with citations
        from reliable agricultural handbooks and extension guides.
      </p>
    </div>
    <div class="fw-source-card">
      <div class="fw-source-head">
        {T.icon("file")}
        <div>
          <div style="font-size:9.5px;letter-spacing:.12em;text-transform:uppercase">Source</div>
          <div style="color:#12211A;font-weight:600">Agriculture Handbook (PDF)</div>
        </div>
        <span class="page">p. 42</span>
      </div>
      <div class="fw-source-body">
        <div class="fw-h3" style="font-size:18px">Wheat Production Guide</div>
        <div>{ui.badge("4.2  Fertilizer Management", "lime")}</div>
        <p style="font-size:13.5px;line-height:1.7">
          In Punjab, urea is recommended in two equal splits: the first at first irrigation
          (about 65-70 kg/acre) and the second at the tillering stage (about 65-70 kg/acre).
        </p>
        <div style="height:110px;border-radius:12px;{T.media('crop_wheat', 0, 0.1)}"></div>
      </div>
    </div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    ui.dark_band(
        "Try the assistant.",
        "Get clear, source-backed answers for your crops, anytime.",
        "Try the assistant",
        cta_dark=True,
    )
    ui.footer()
