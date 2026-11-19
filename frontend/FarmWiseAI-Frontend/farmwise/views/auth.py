"""Auth screens: create account, verify, resend, log in, forgot, reset."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import theme as T
from farmwise.routes import go, href


def _mask(email: str) -> str:
    name, _, domain = (email or "farmer@example.com").partition("@")
    return f"{name[:1]}•••@{domain}"


def _frame() -> None:
    """Common page shell (background + back link)."""
    T.show(
        f"""
<div class="fw-auth-topbar" style="padding-top:6px">
  {ui.logo()}
  <a class="fw-link" href="{href('home')}">Back to site</a>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- create account


def signup() -> None:
    _frame()
    with st.container(key="authsplit"):
        left, right = st.columns([1, 1.2], gap="small")
        with left:
            T.show(
                f'<div class="fw-auth-art" style="{T.media("field", 0, 0.15)}"></div>',
                unsafe_allow_html=True,
            )
        with right:
            T.show(
                f"""
<div class="fw-auth-art-head">{ui.logo()}
  <h1 class="fw-auth-head" style="margin-top:26px">Create your account</h1>
</div>
""",
                unsafe_allow_html=True,
            )
            with st.form("signup_form", border=False):
                name = st.text_input(
                    "Full name", placeholder="Full name", label_visibility="collapsed", key="su_name"
                )
                email = st.text_input(
                    "Email", placeholder="Email", label_visibility="collapsed", key="su_email"
                )
                password = st.text_input(
                    "Password",
                    placeholder="Password",
                    type="password",
                    label_visibility="collapsed",
                    key="su_password",
                )
                create = st.form_submit_button("Create account", type="primary", width="stretch")
            T.show(
                '<p class="fw-small" style="text-align:center;margin:14px 0 4px">'
                f'Already have an account? <a href="{href("login")}" style="font-weight:600;color:var(--text)">Log in</a></p>',
                unsafe_allow_html=True,
            )
            if create:
                if not name or not email or not password:
                    st.error("Please fill in your name, email and password.")
                else:
                    st.session_state.pending_email = email
                    st.session_state.account = {"name": name, "email": email}
                    go("verify")


# ------------------------------------------------------------------- verify email


def verify() -> None:
    _frame()
    with st.container(key="authplain"):
        T.show(
            f"""
<div style="text-align:center">
  {ui.logo()}
  <div style="display:grid;place-items:center;margin:22px 0 10px;color:var(--ink)">{T.icon("mail", "fw-service-icon")}</div>
  <h1 class="fw-auth-head" style="text-align:center">Verify your email</h1>
  <p class="fw-small" style="text-align:center">
    Check your inbox or spam folder.<br>
    Enter the 6-digit code sent to <strong>{_mask(st.session_state.pending_email)}</strong>.
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
        with st.container(key="otp"):
            cols = st.columns(6, gap="small")
            digits = [
                cols[i].text_input(
                    f"Digit {i + 1}",
                    max_chars=1,
                    key=f"otp_{i}",
                    label_visibility="collapsed",
                    placeholder="•",
                )
                for i in range(6)
            ]
        st.write("")
        if st.button("Verify email", type="primary", width="stretch", key="verify_btn"):
            code = "".join(digits).strip()
            if len(code) != 6:
                st.error("Enter all 6 digits of the code.")
            else:
                st.session_state.account = st.session_state.account or {
                    "name": "Farmer",
                    "email": st.session_state.pending_email,
                }
                go("dashboard")
        T.show(
            '<p class="fw-small" style="text-align:center;margin-top:12px">'
            "Didn't get a code? "
            f'<a href="{href("resend")}" style="font-weight:600;color:var(--text);text-decoration:underline">Resend code</a></p>',
            unsafe_allow_html=True,
        )


def resend() -> None:
    _frame()
    with st.container(key="authplain"):
        T.show(
            f"""
<div style="text-align:center">
  {ui.logo()}
  <div style="display:grid;place-items:center;margin:22px 0 10px;color:var(--ink)">{T.icon("mail", "fw-service-icon")}</div>
  <h1 class="fw-auth-head" style="text-align:center">Resend verification code</h1>
  <p class="fw-small" style="text-align:center">
    We'll send a new code to <strong>{_mask(st.session_state.pending_email)}</strong>.
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Send new code", type="primary", width="stretch", key="resend_btn"):
            st.success("A new 6-digit code has been sent. It expires in 10 minutes.")
        if st.button("Back to verification", width="stretch", key="back_verify"):
            go("verify")


# ------------------------------------------------------------------------- login


def login() -> None:
    _frame()
    with st.container(key="authsplit"):
        left, right = st.columns([1, 1.2], gap="small")
        with left:
            T.show(
                f'<div class="fw-auth-art" style="{T.media("farmer", 0, 0.12)}"></div>',
                unsafe_allow_html=True,
            )
        with right:
            T.show(
                f"""
<div class="fw-auth-art-head">{ui.logo()}
  <h1 class="fw-auth-head" style="margin-top:26px">Log in to<br>FarmWiseAI</h1>
</div>
""",
                unsafe_allow_html=True,
            )
            with st.form("login_form", border=False):
                email = st.text_input(
                    "Email", placeholder="Email", label_visibility="collapsed", key="li_email"
                )
                password = st.text_input(
                    "Password",
                    placeholder="Password",
                    type="password",
                    label_visibility="collapsed",
                    key="li_password",
                )
                T.show(
                    f'<p style="margin:2px 0 10px"><a class="fw-small" href="{href("forgot")}" '
                    'style="text-decoration:underline;font-weight:600;color:var(--text)">Forgot password?</a></p>',
                    unsafe_allow_html=True,
                )
                submit = st.form_submit_button("Log in", type="primary", width="stretch")
            T.show(
                '<p class="fw-small" style="text-align:center;margin:14px 0 4px">'
                f'New here? <a href="{href("signup")}" style="font-weight:600;color:var(--text)">Create an account</a></p>',
                unsafe_allow_html=True,
            )
            if submit:
                if not email or not password:
                    st.error("Enter your email and password to continue.")
                else:
                    st.session_state.account = {"name": email.split("@")[0].title(), "email": email}
                    go("dashboard")


# --------------------------------------------------------------- password reset


def forgot() -> None:
    _frame()
    with st.container(key="authplain"):
        T.show(
            f"""
<div style="text-align:center">
  {ui.logo()}
  <h1 class="fw-auth-head" style="text-align:center;margin-top:26px">Forgot password?</h1>
  <p class="fw-small" style="text-align:center">
    Enter your email and we'll send you a link to reset your password.
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
        with st.form("forgot_form", border=False):
            email = st.text_input(
                "Email", placeholder="Email", label_visibility="collapsed", key="fo_email"
            )
            sent = st.form_submit_button("Send reset link", type="primary", width="stretch")
        if sent:
            if not email:
                st.error("Enter the email linked to your account.")
            else:
                st.session_state.pending_email = email
                st.info("Reset link sent. Check your inbox to continue.")
                go("reset")


def reset() -> None:
    _frame()
    with st.container(key="authplain"):
        T.show(
            f"""
<div style="text-align:center">
  {ui.logo()}
  <h1 class="fw-auth-head" style="text-align:center;margin-top:26px">Reset your password</h1>
  <p class="fw-small" style="text-align:center">Choose a new password for your FarmWiseAI account.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        with st.form("reset_form", border=False):
            pw1 = st.text_input(
                "New password",
                placeholder="New password",
                type="password",
                label_visibility="collapsed",
                key="rp_pass",
            )
            pw2 = st.text_input(
                "Confirm password",
                placeholder="Confirm password",
                type="password",
                label_visibility="collapsed",
                key="rp_confirm",
            )
            done = st.form_submit_button("Reset password", type="primary", width="stretch")
        if done:
            if len(pw1) < 8:
                st.error("Use at least 8 characters for your password.")
            elif pw1 != pw2:
                st.error("Passwords do not match.")
            else:
                st.success("Password updated. You can log in now.")
                go("login")
