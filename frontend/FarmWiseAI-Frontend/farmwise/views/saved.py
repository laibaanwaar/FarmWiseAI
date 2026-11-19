"""Saved answers - cards with a citation dialog."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import rag
from farmwise import theme as T
from farmwise.data import SAVED


@st.dialog("Saved answer · source")
def _citation(entry_id: str, lang: str) -> None:
    entry = rag.entry_by_id(entry_id)
    if not entry:
        st.write("Source not found.")
        return
    T.show(f"**{entry['doc']}** &nbsp;·&nbsp; page {entry['printed_page']}")
    T.show(f"#### {entry['heading']}")
    st.caption(entry["section"])
    st.info(entry[f"snippet_{lang}"])
    st.caption(f"PDF page {entry['page']} · Printed page {entry['printed_page']}")


def render() -> None:
    with st.container(key="appframe"):
        ui.app_nav("saved")

        T.show(
            """
<h1 class="fw-admin-title">Saved Answers</h1>
<p class="fw-admin-sub">Your saved, trusted answers with sources.</p>
""",
            unsafe_allow_html=True,
        )

        cols = st.columns(3, gap="medium")
        for index, item in enumerate(SAVED[:3]):
            with cols[index]:
                with st.container(key=f"saved_{index}"):
                    T.show(
                        f"""
<div style="height:150px;{T.media(item['image'], 0, 0.1)}"></div>
<div style="padding:14px 16px 4px">
  <span class="fw-chip">{T.icon('leaf')}{item['crop']}</span>
  <div class="fw-h4" style="margin-top:10px;font-size:15px">{item['title']}</div>
  <p class="fw-small" style="margin-top:6px;min-height:38px">{item['blurb']}</p>
</div>
""",
                        unsafe_allow_html=True,
                    )
                    if st.button("View citation", key=f"cite_{index}", icon=":material/menu_book:"):
                        _citation(item["id"], st.session_state.chat_lang)

        st.write("")
        T.show(
            f"""
<div class="fw-panel" style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap">
  <div>
    <div class="fw-h3">Keep building your field notebook</div>
    <p class="fw-small" style="margin-top:4px">Every answer you save keeps its handbook citation for later.</p>
  </div>
  <a class="fw-btn fw-btn-lime" href="/chat">Ask a crop question {T.icon("arrow")}</a>
</div>
""",
            unsafe_allow_html=True,
        )
