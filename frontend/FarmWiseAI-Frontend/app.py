"""FarmWiseAI - Streamlit frontend.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from farmwise import state, theme
from farmwise.pages import registry

st.set_page_config(
    page_title="FarmWiseAI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="auto",
)

theme.inject()
state.init()

navigation = st.navigation(list(registry().values()), position="hidden")
navigation.run()
