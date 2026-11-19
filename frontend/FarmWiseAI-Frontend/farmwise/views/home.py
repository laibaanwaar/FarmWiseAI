"""Landing page - 'Field answers, backed by sources.'"""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.data import CROPS
from farmwise.routes import href


def _chat_preview() -> str:
    return f"""
<div class="fw-chatcard">
  <div class="fw-chatcard-head">
    {T.icon("leaf")}
    <span style="color:#12211A;font-weight:700">FarmWiseAI Assistant</span>
    <span class="right">EN / اردو</span>
  </div>
  <div class="fw-chatcard-body">
    <div class="fw-msg user">
      <span class="fw-msg-av">You</span>
      <div class="fw-bubble">What is the right time and rate for urea in wheat?</div>
    </div>
    <div class="fw-msg">
      <span class="fw-msg-av">{T.icon("leaf")}</span>
      <div class="fw-bubble">
        For wheat in Punjab, apply urea in two splits:
        <ul>
          <li>1st: at first irrigation (about 65-70 kg/acre)</li>
          <li>2nd: at the tillering stage (about 65-70 kg/acre)</li>
        </ul>
        <p style="margin-top:6px">This helps strong tillering and a higher yield.</p>
      </div>
    </div>
    <div class="fw-msg user">
      <span class="fw-msg-av">You</span>
      <div class="fw-bubble" style="font-size:12.5px">گندم میں یوریا کب اور کتنی مقدار میں ڈالنی ہے؟</div>
    </div>
    <div class="fw-msg">
      <span class="fw-msg-av">{T.icon("leaf")}</span>
      <div class="fw-bubble">
        <div class="fw-ur" style="font-size:12.5px;margin-top:0">
          پنجاب میں گندم کے لیے یوریا دو حصوں میں ڈالیں: پہلی بار پہلی آبپاشی پر (تقریباً 65-70 کلوگرام فی ایکڑ)، دوسری بار ٹلرنگ کے مرحلے پر۔
        </div>
      </div>
    </div>
    <div class="fw-chatcard-head" style="border-bottom:0;border-top:1px solid var(--line);padding:10px 4px 0">
      <span style="color:#8A9389">Ask a question about your crop...</span>
      <span class="right" style="background:var(--lime);border-color:var(--lime);color:#12211A">{T.icon("send")}</span>
    </div>
  </div>
</div>"""


def _source_preview() -> str:
    return f"""
<div class="fw-source-card">
  <div class="fw-source-head">
    {T.icon("file")}
    <div><div style="font-size:9.5px;letter-spacing:.12em;text-transform:uppercase">Source</div>
    <div style="color:#12211A;font-weight:600">Agriculture Handbook (PDF)</div></div>
    <span class="page">p. 42</span>
  </div>
  <div class="fw-source-body">
    <div class="fw-h3" style="font-size:17px">Wheat Production Guide</div>
    <div>{ui.badge("4.2  Fertilizer Management", "lime")}</div>
    <p style="font-size:13px;line-height:1.65">In Punjab, urea is recommended in two equal splits: the first at first irrigation (about 65-70 kg/acre) and the second at the tillering stage (about 65-70 kg/acre).</p>
    <div class="fw-source-media" style="{T.media('wheat_close', 0, 0.1)}"></div>
  </div>
</div>"""


def render() -> None:
    ui.top_nav("home")

    ui.hero(
        "Field answers,<br>backed by sources.",
        "An agricultural AI assistant with trusted, source-grounded guidance for Pakistan's farmers.",
    )

    ui.metrics(
        [
            ("5", "Major crops covered"),
            ("10", "Handbook topics in the knowledge base"),
            ("2", "Languages &mdash; English &amp; اردو"),
            ("100<span>%</span>", "Answers come with sources"),
        ]
    )

    T.show(
        """
<section class="fw-section">
  <div class="fw-split" style="margin-bottom:44px">
    <h2 class="fw-h2" style="margin:0">Practical, reliable<br>crop guidance<br>for higher yields.</h2>
    <p class="fw-sub fw-split-rule" style="color:var(--muted)">
      Get instant, source-backed answers on crop care, pest and disease management,
      fertilizer use, and best practices &mdash; tailored for Pakistan's conditions.
    </p>
  </div>
  <div class="fw-grid grid-3">
"""
        + "".join(ui.crop_tile(c["name"], c["image"]) for c in CROPS[:3])
        + """
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    T.show(
        f"""
<section class="fw-section dark">
  <h2 class="fw-h2" style="max-width:560px">Ask, get a trusted answer,<br>with the source.</h2>
  <p class="fw-sub" style="margin-bottom:34px">
    A bilingual (English &amp; Urdu) assistant that gives clear, practical advice with citations
    from reliable agricultural handbooks and extension guides.
  </p>
  <div class="fw-grid grid-2" style="align-items:stretch">
    {_chat_preview()}
    {_source_preview()}
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    T.show(
        f"""
<section class="fw-section">
  <div class="fw-trust">
    <div class="fw-trust-art">
      <div class="fw-trust-media" style="{T.media('farmer', 0.15, 0.4, 'center 24%')}"></div>
      <div class="fw-trust-float">
        <div class="fw-trust-float-head">{T.icon("shield")}<span>Every answer cited</span></div>
        <p>Wheat Production Guide &middot; Agriculture Handbook &middot; p. 42</p>
        <div class="fw-trust-bar"><span></span></div>
      </div>
    </div>
    <div>
      <span class="fw-eyebrow">Why FarmWiseAI</span>
      <h2 class="fw-h2">Advice you can<br>act on with<br>confidence.</h2>
      <p class="fw-sub" style="color:var(--muted)">
        FarmWiseAI turns agricultural handbooks into clear, practical answers
        for your fields &mdash; without the guesswork.
      </p>
      <div class="fw-checklist">
        <div class="fw-check">
          <span class="fw-check-ico">{T.icon("check")}</span>
          <div>
            <strong>Grounded in handbooks</strong>
            <p>Every answer is retrieved from trusted extension guides, not invented.</p>
          </div>
        </div>
        <div class="fw-check">
          <span class="fw-check-ico">{T.icon("file")}</span>
          <div>
            <strong>Citations you can check</strong>
            <p>Each reply shows the document, PDF page and section it came from.</p>
          </div>
        </div>
        <div class="fw-check">
          <span class="fw-check-ico">{T.icon("book")}</span>
          <div>
            <strong>Bilingual by design</strong>
            <p>Ask in English or Urdu and get the answer in the language you choose.</p>
          </div>
        </div>
      </div>
      <a class="fw-btn fw-btn-dark" href="{href('chat')}">Ask a crop question {T.icon("arrow")}</a>
    </div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    ui.dark_band(
        "Try the FarmWiseAI assistant today.",
        "Get clear, source-backed answers for your crops, anytime.",
        "Ask a crop question",
        cta_dark=True,
    )
    ui.footer()
