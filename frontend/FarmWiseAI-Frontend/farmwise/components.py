
"""Reusable HTML/Streamlit building blocks shared by every page."""

from __future__ import annotations

import streamlit as st

from farmwise import theme as T
from farmwise.routes import go, href



def logo(light: bool = False, page: str = "home", size: str | None = None) -> str:
    style = f' style="font-size:{size}"' if size else ""
    klass = "fw-logo fw-logo-light" if light else "fw-logo"
    return f'<a class="{klass}" href="{href(page)}" target="_self"{style}>{T.icon("leaf")}<span>FarmWiseAI</span></a>'


# --------------------------------------------------------------------- marketing




def top_nav(active: str) -> None:
    items = [
        ("home", "Home"),
        ("about", "About Us"),
        ("services", "Services"),
        ("crops", "Crops"),
    ]

    links = "".join(
        f'<a class="fw-nav-link{" is-active" if slug == active else ""}" href="{href(slug)}" target="_self">{label}</a>'
        for slug, label in items
    )

    T.show(
        f"""
<header class="fw-nav">
  <div class="fw-nav-inner">
    {logo()}
    <nav class="fw-nav-links">{links}</nav>
    <div class="fw-nav-actions">
      <a class="fw-nav-quiet" href="{href('signup')}" target="_self">
        Sign up
      </a>
      <a class="fw-btn fw-btn-lime fw-btn-sm" href="{href('chat')}" target="_self">
        Try the assistant
      </a>
    </div>
  </div>
</header>
""",
        unsafe_allow_html=True,
    )



def hero(
    title_html: str,
    sub: str,
    image: str = "hero_field",
    cta: tuple[str, str] | None = ("Ask a crop question", "chat"),
    secondary: tuple[str, str] | None = None,
    tall: bool = False,
    eyebrow: str | None = None,
    cta_params: dict | None = None,
) -> None:
    actions = ""
    if cta:
        actions += (
            f'<a class="fw-btn fw-btn-lime" href="{href(cta[1], **(cta_params or {}))}">'
            f"{cta[0]} {T.icon('arrow')}</a>"
        )
    if secondary:
        actions += (
            f'<a class="fw-btn fw-btn-outline-light" href="{href(secondary[1])}">'
            f"{secondary[0]} {T.icon('arrow')}</a>"
        )
    eyebrow_html = f'<span class="fw-eyebrow">{eyebrow}</span>' if eyebrow else ""
    T.show(
        f"""
<section class="fw-hero{' fw-hero-tall' if tall else ''}" style="{T.media(image)}">
  <div class="fw-hero-copy">
    {eyebrow_html}
    <h1 class="fw-h1">{title_html}</h1>
    <p class="fw-sub">{sub}</p>
    <div class="fw-actions">{actions}</div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def crop_tile(name: str, image: str, page: str = "crops") -> str:
    return (
        f'<a class="fw-crop-tile" href="{href(page)}" style="{T.media(image, 0.05, 0.35)}">'
        f"<h3>{name}</h3>{T.icon('arrow', 'fw-arrow')}</a>"
    )


def metrics(items: list[tuple[str, str]]) -> None:
    cells = "".join(
        f'<div class="fw-metric"><div class="fw-metric-value">{value}</div>'
        f'<div class="fw-metric-label">{label}</div></div>'
        for value, label in items
    )
    T.show(f'<section class="fw-metrics-wrap"><div class="fw-metrics">{cells}</div></section>', unsafe_allow_html=True)


def service_card(icon_name: str, title: str, text: str, image: str) -> str:
    return f"""
<article class="fw-card fw-service">
  <div class="fw-card-body">
    {T.icon(icon_name, 'fw-service-icon')}
    <h3>{title}</h3>
    <p>{text}</p>
  </div>
  <div class="fw-card-media" style="{T.media(image, 0, 0.15)}"></div>
</article>"""


def dark_band(title_html: str, text: str, cta_label: str, cta_page: str = "chat", cta_dark: bool = False) -> None:
    btn_class = "fw-btn-dark" if cta_dark else "fw-btn-lime"
    T.show(
        f"""
<section class="fw-section lime tight">
  <div class="fw-row-between">
    <h2 class="fw-h2" style="margin:0">{title_html}</h2>
    <div class="fw-row" style="gap:26px">
      <p class="fw-small" style="max-width:34ch;color:#27401A">{text}</p>
      <a class="fw-btn {btn_class}" href="{href(cta_page)}">{cta_label} {T.icon('arrow')}</a>
    </div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def footer() -> None:
    links = "".join(
        f'<a href="{href(slug)}">{label}</a>'
        for slug, label in [("home", "Home"), ("about", "About Us"), ("services", "Services"), ("crops", "Crops")]
    )
    T.show(
        f"""
<footer class="fw-footer">
  <div class="fw-footer-inner">
    {logo(light=True)}
    <nav class="fw-footer-links">{links}</nav>
    <div class="fw-footer-meta"><span>Pakistan</span><span class="fw-divider-v"></span><span>EN / اردو</span></div>
  </div>
</footer>
""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- app chrome


def app_nav(active: str, signed_in: bool = False) -> None:
    links = [
        ("Dashboard", "dashboard", "nav_dashboard"),
        ("Saved Answers", "saved", "nav_saved"),
        ("New chat", "chat", "nav_newchat"),
        ("Account", "account", "nav_account"),
    ]
    with st.container(key="appnav"):
        brand, menu = st.columns([1.4, 5], vertical_alignment="center", gap="small")
        with brand:
            T.show(logo(light=True, size="17px"), unsafe_allow_html=True)
        with menu:
            with st.container(horizontal=True, horizontal_alignment="right", gap="small", key="appnavlinks"):
                for label, slug, key in links:
                    if st.button(
                        label,
                        key=key,
                        type="primary" if active == slug else "secondary",
                    ):
                        go(slug)


def stat_card(icon_name: str, label: str, value: str, dark: bool = False) -> str:
    return f"""
<div class="fw-stat{' dark' if dark else ''}">
  <div>{T.icon(icon_name, 'fw-stat-icon')}</div>
  <div>
    <div class="fw-stat-label">{label}</div>
    <div class="fw-stat-value">{value}</div>
  </div>
</div>"""


def badge(text: str, variant: str = "", icon_name: str | None = None) -> str:
    klass = f"fw-badge {variant}".strip()
    glyph = T.icon(icon_name) if icon_name else ""
    return f'<span class="{klass}">{glyph}{text}</span>'


def who(name: str, email: str = "", size: str | None = None) -> str:
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "?"
    style = f' style="width:{size};height:{size};flex-basis:{size}"' if size else ""
    mail = f"<small>{email}</small>" if email else ""
    return f'<div class="fw-who"><span class="fw-av"{style}>{initials}</span><div><strong>{name}</strong>{mail}</div></div>'


def answer_html(answer: dict, lang: str = "en") -> str:
    """Render a retrieval answer (shared by chat + previews)."""
    intro = answer[f"intro_{lang}"]
    bullets = answer[f"bullets_{lang}"]
    closing = answer.get(f"closing_{lang}", "")
    items = "".join(f"<li>{b}</li>" for b in bullets)
    close = f"<p style='margin-top:6px'>{closing}</p>" if closing else ""
    return f"<p>{intro}</p><ul>{items}</ul>{close}"
