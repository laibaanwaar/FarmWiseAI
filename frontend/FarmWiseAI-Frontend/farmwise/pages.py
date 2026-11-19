"""Single registry of every page - imported by app.py and by routes.go()."""

from __future__ import annotations

import streamlit as st

from farmwise.routes import PATHS

_REGISTRY: dict[str, st.Page] = {}  # type: ignore[attr-defined]


def registry() -> dict:
    global _REGISTRY
    if _REGISTRY:
        return _REGISTRY

    from farmwise.views import about, admin,  chat, crops, dashboard, home, saved, services

    _REGISTRY = {
        "home": st.Page(home.render, title="FarmWiseAI", default=True),
        "services": st.Page(services.render, title="Services", url_path=PATHS["services"]),
        "crops": st.Page(crops.render, title="Crops", url_path=PATHS["crops"]),
        "about": st.Page(about.render, title="About Us", url_path=PATHS["about"]),
        "dashboard": st.Page(dashboard.render, title="Dashboard", url_path=PATHS["dashboard"]),
        "chat": st.Page(chat.render, title="Crop assistant", url_path=PATHS["chat"]),
        "saved": st.Page(saved.render, title="Saved answers", url_path=PATHS["saved"]),
        "admin": st.Page(admin.overview, title="Admin overview", url_path=PATHS["admin"]),
        "admin_users": st.Page(admin.users, title="Users & roles", url_path=PATHS["admin_users"]),
        "admin_audit": st.Page(admin.audit, title="Audit activity", url_path=PATHS["admin_audit"]),
        "admin_settings": st.Page(admin.settings, title="Settings", url_path=PATHS["admin_settings"]),
    }
    return _REGISTRY
