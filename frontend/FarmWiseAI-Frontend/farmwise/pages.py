"""Single registry of every page - imported by app.py and by routes.go()."""

from __future__ import annotations

from functools import wraps

import streamlit as st

from farmwise.routes import PATHS

_REGISTRY: dict[str, st.Page] = {}  # type: ignore[attr-defined]


def _protected(view, *, admin_only: bool = False):
    @wraps(view)
    def guarded():
        from farmwise.views.auth import require_authenticated

        if require_authenticated(admin_only=admin_only):
            view()

    return guarded


def registry() -> dict:
    global _REGISTRY
    if _REGISTRY:
        return _REGISTRY

    from farmwise.views import about, admin, auth, chat, crops, dashboard, home, saved, services

    _REGISTRY = {
        "home": st.Page(home.render, title="FarmWiseAI", default=True),
        "services": st.Page(services.render, title="Services", url_path=PATHS["services"]),
        "crops": st.Page(crops.render, title="Crops", url_path=PATHS["crops"]),
        "about": st.Page(about.render, title="About Us", url_path=PATHS["about"]),
        "signup": st.Page(auth.signup, title="Create account", url_path=PATHS["signup"]),
        "verify": st.Page(auth.verify, title="Verify email", url_path=PATHS["verify"]),
        "resend": st.Page(auth.resend, title="Resend code", url_path=PATHS["resend"]),
        "login": st.Page(auth.login, title="Log in", url_path=PATHS["login"]),
        "account": st.Page(auth.account, title="Account", url_path=PATHS["account"]),
        "forgot": st.Page(auth.forgot, title="Forgot password", url_path=PATHS["forgot"]),
        "reset": st.Page(auth.reset, title="Reset password", url_path=PATHS["reset"]),
        "dashboard": st.Page(_protected(dashboard.render), title="Dashboard", url_path=PATHS["dashboard"]),
        "chat": st.Page(_protected(chat.render), title="Crop assistant", url_path=PATHS["chat"]),
        "saved": st.Page(_protected(saved.render), title="Saved answers", url_path=PATHS["saved"]),
        "admin": st.Page(_protected(admin.overview, admin_only=True), title="Admin overview", url_path=PATHS["admin"]),
        "admin_users": st.Page(_protected(admin.users, admin_only=True), title="Users & roles", url_path=PATHS["admin_users"]),
        "admin_audit": st.Page(_protected(admin.audit, admin_only=True), title="Audit activity", url_path=PATHS["admin_audit"]),
        "admin_settings": st.Page(_protected(admin.settings, admin_only=True), title="Settings", url_path=PATHS["admin_settings"]),
    }
    return _REGISTRY
