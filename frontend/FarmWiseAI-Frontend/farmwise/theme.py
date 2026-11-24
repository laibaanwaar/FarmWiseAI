"""Design tokens, global CSS injection, inline SVG icons and image helpers."""

from __future__ import annotations

import base64
import pathlib
import textwrap
import re

import streamlit as st

PKG = pathlib.Path(__file__).resolve().parent
ROOT = PKG.parent
ASSETS = ROOT / "assets"
CSS_FILE = PKG / "styles.css"

INK = "#0E2118"
LIME = "#C9F45B"
CREAM = "#F8F7EF"

# Fallback artwork: warm, photographic gradients used whenever a matching file is
# missing from /assets (hero_field.jpg, crop_wheat.jpg, farmer.jpg, ...).
GRADIENTS = {
    "hero_field": (
        "radial-gradient(120% 120% at 78% 8%, #E8DFAF 0%, #BFCE86 22%, "
        "#7FA155 48%, #3F6631 76%, #1B3520 100%)"
    ),
    "field": (
        "linear-gradient(165deg, #DCE6B8 0%, #93B269 35%, #4F7A3E 70%, #22401F 100%)"
    ),
    "farmer": (
        "radial-gradient(110% 100% at 70% 15%, #F0DFB4 0%, #C9B27A 30%, "
        "#7E8A4C 62%, #2D4526 100%)"
    ),
    "crop_wheat": (
        "radial-gradient(120% 90% at 60% 5%, #F4E9A6 0%, #CFD173 28%, "
        "#8FAC4B 62%, #3E6428 100%)"
    ),
    "crop_rice": (
        "radial-gradient(120% 90% at 60% 5%, #E6EFB4 0%, #B4CE74 30%, "
        "#6E9C42 64%, #2C4B22 100%)"
    ),
    "crop_cotton": (
        "radial-gradient(120% 90% at 65% 10%, #FBF7EA 0%, #E7E6CE 32%, "
        "#A9B486 66%, #41552F 100%)"
    ),
    "crop_sugarcane": (
        "radial-gradient(120% 90% at 55% 10%, #E7EFC4 0%, #B7CB77 32%, "
        "#6E9440 66%, #2F4A21 100%)"
    ),
    "crop_maize": (
        "radial-gradient(120% 90% at 55% 10%, #F3E9B0 0%, #D3CE72 30%, "
        "#8AA544 64%, #36521F 100%)"
    ),
    "soil": (
        "radial-gradient(110% 100% at 60% 10%, #C9A574 0%, #8C6438 40%, #513520 78%, #2A1D12 100%)"
    ),
    "water": (
        "radial-gradient(110% 100% at 55% 10%, #BFD9D2 0%, #77A596 38%, #3E6E5C 72%, #1D3A2E 100%)"
    ),
    "disease": (
        "radial-gradient(110% 100% at 55% 10%, #D6DDA6 0%, #8FA35A 38%, #4A6430 74%, #23361B 100%)"
    ),
    "handbook": (
        "radial-gradient(110% 100% at 50% 20%, #DCD6BC 0%, #A39C71 38%, #5B5738 74%, #2C2A1B 100%)"
    ),
    "wheat_close": (
        "radial-gradient(120% 100% at 70% 5%, #F6EAB0 0%, #D5D585 30%, #8CAA4C 66%, #3B6026 100%)"
    ),
    "portrait": (
        "radial-gradient(110% 100% at 60% 12%, #F1E0C0 0%, #CBB481 36%, #8C8550 68%, #37411F 100%)"
    ),
    "default": (
        "linear-gradient(150deg, #DCE7BE 0%, #A9C27D 34%, #5F8A48 68%, #24401E 100%)"
    ),
}

_EXT_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

@st.cache_data(show_spinner=False)
def asset_uri(key: str) -> str | None:
    """Return a data URI for assets/<key>.<ext> if the file exists."""
    for ext, mime in _EXT_MIME.items():
        path = ASSETS / f"{key}{ext}"
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    return None


def media(key: str, top: float = 0.0, bottom: float = 0.0, position: str = "center") -> str:
    """Inline `background-*` style string: local photo if available, else gradient."""
    scrim = ""
    if top or bottom:
        scrim = (
            f"linear-gradient(180deg, rgba(10,26,18,{top}) 0%, "
            f"rgba(10,26,18,{bottom}) 100%), "
        )
    uri = asset_uri(key)
    layer = f"url('{uri}')" if uri else GRADIENTS.get(key, GRADIENTS["default"])
    return (
        f"background-image:{scrim}{layer};"
        f"background-size:cover;background-position:{position};"
    )


@st.cache_data(show_spinner=False)
def load_css(version: int | None = None) -> str:
    # Include the stylesheet timestamp in the cache key so CSS edits are picked
    # up by a running Streamlit session on its next rerun.
    del version
    return CSS_FILE.read_text(encoding="utf-8")


def inject() -> None:
    st.markdown(
        f"<style>{load_css(CSS_FILE.stat().st_mtime_ns)}</style>",
        unsafe_allow_html=True,
    )


def show(markup: str, *args, **kwargs) -> None:
    """Render an HTML fragment with same-tab internal navigation."""
    flat = "\n".join(
        line.lstrip()
        for line in textwrap.dedent(markup or "").splitlines()
    ).strip()

    # Make all HTML links open in the current tab.
    flat = re.sub(
        r'(<a\b[^>]*?)\s+target=(["\']).*?\2',
        r'\1 target="_self"',
        flat,
        flags=re.IGNORECASE,
    )

    flat = re.sub(
        r'<a\b(?![^>]*\btarget\s*=)',
        '<a target="_self"',
        flat,
        flags=re.IGNORECASE,
    )

    st.markdown(flat, unsafe_allow_html=True)


_SPRITE: dict[str, str] = {
    "leaf": '<path d="M4 20c0-8.5 6.5-15 16-16 0 10.5-6.5 16-16 16z"/><path d="M4 20c4.2-4.4 8.4-6.6 12.5-8.5"/>',
    "arrow": '<line x1="4" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    "arrow-up": '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16.5 3.13a4 4 0 0 1 0 7.75"/>',
    "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "gear": '<circle cx="12" cy="12" r="3.2"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.55V21a2 2 0 0 1-4 0v-.1A1.7 1.7 0 0 0 9 19.35a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.65 15a1.7 1.7 0 0 0-1.55-1.03H3a2 2 0 0 1 0-4h.1A1.7 1.7 0 0 0 4.65 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.65 1.7 1.7 0 0 0 10 3.1V3a2 2 0 0 1 4 0v.1A1.7 1.7 0 0 0 15 4.65a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.35 9c.24.62.83 1.03 1.55 1.03H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "search": '<circle cx="11" cy="11" r="7.5"/><line x1="21" y1="21" x2="16.7" y2="16.7"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "close": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2.5"/><polyline points="22 6.5 12 13.5 2 6.5"/>',
    "lock": '<rect x="3" y="10.5" width="18" height="11" rx="2.5"/><path d="M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5"/>',
    "eye": '<path d="M1.5 12S5.5 4.5 12 4.5 22.5 12 22.5 12 18.5 19.5 12 19.5 1.5 12 1.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "send": '<line x1="21" y1="3" x2="10.5" y2="13.5"/><polygon points="21 3 14.5 21 10.5 13.5 3 9.5 21 3"/>',
    "file": '<path d="M14 2H6.5A2.5 2.5 0 0 0 4 4.5v15A2.5 2.5 0 0 0 6.5 22h11A2.5 2.5 0 0 0 20 19.5V8z"/><polyline points="14 2 14 8 20 8"/><line x1="15.5" y1="13" x2="8.5" y2="13"/><line x1="15.5" y1="17" x2="8.5" y2="17"/>',
    "book": '<path d="M2 3.5h6a4 4 0 0 1 4 4V21a3 3 0 0 0-3-3H2z"/><path d="M22 3.5h-6a4 4 0 0 0-4 4V21a3 3 0 0 1 3-3h7z"/>',
    "drop": '<path d="M12 2.7l5.4 5.6a7.7 7.7 0 1 1-10.8 0z"/>',
    "bug": '<rect x="8" y="6.5" width="8" height="13" rx="4"/><path d="M19 7.5l-3 1.8M5 7.5l3 1.8M19 18l-3-1.8M5 18l3-1.8M12 19.5v-6M3 12.5h3.6M17.4 12.5H21"/>',
    "seedling": '<path d="M12 21v-9"/><path d="M12 12C12 7.6 8.7 4.5 4 4.5c0 4.4 3.3 7.5 8 7.5z"/><path d="M12 15c0-4.4 3.3-7.5 8-7.5 0 4.4-3.3 7.5-8 7.5z"/>',
    "bag": '<path d="M6.5 8h11l1.4 11a2 2 0 0 1-2 2.2H7.1a2 2 0 0 1-2-2.2z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    "wheat": '<path d="M12 22V9"/><path d="M12 9c0-2.6 1.7-4.6 3.6-5.6-.9 2.6-.9 4.4 0 6.6"/><path d="M12 9c0-2.6-1.7-4.6-3.6-5.6.9 2.6.9 4.4 0 6.6"/><path d="M12 14.5c0-2.6 1.7-4.6 3.6-5.6-.9 2.6-.9 4.4 0 6.6"/><path d="M12 14.5c0-2.6-1.7-4.6-3.6-5.6.9 2.6.9 4.4 0 6.6"/>',
    "shield": '<path d="M12 22s8-3.6 8-10V5.5L12 2 4 5.5V12c0 6.4 8 10 8 10z"/>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "dots": '<circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
    "external": '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2.5"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="3" x2="8" y2="7"/><line x1="16" y1="3" x2="16" y2="7"/>',
    "bolt": '<polygon points="13 2 4 14 11 14 10 22 20 10 13 10 13 2"/>',
}


def icon(name: str, cls: str = "") -> str:
    body = _SPRITE.get(name, _SPRITE["leaf"])
    klass = f"fw-ico {cls}".strip()
    return (
        f'<svg class="{klass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{body}</svg>'
    )
