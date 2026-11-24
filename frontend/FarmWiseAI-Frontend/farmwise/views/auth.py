"""Auth screens: create account, verify, resend, log in, forgot, reset."""

from __future__ import annotations

import html
import re

import streamlit as st

from farmwise import auth_api
from farmwise.api_client import APIError
from farmwise import components as ui
from farmwise import theme as T
from farmwise.routes import go, href


def _show_api_error(exc: APIError) -> None:
    message = exc.message
    if exc.retry_after:
        message += f" You can try again in {exc.retry_after}."
    elif exc.retryable and "try again" not in message.casefold():
        message += " Please retry shortly."
    st.error(message)


def _distribute_pasted_otp() -> None:
    """Split a pasted six-digit value from any OTP box across all six boxes."""
    for index in range(6):
        candidate = str(st.session_state.get(f"otp_{index}", "") or "").strip()
        if len(candidate) == 6 and candidate.isdigit():
            for digit_index, digit in enumerate(candidate):
                st.session_state[f"otp_{digit_index}"] = digit
            break


def _clear_otp_inputs() -> None:
    for index in range(6):
        st.session_state.pop(f"otp_{index}", None)


def _clear_auth_widgets() -> None:
    for key in ("su_name", "su_email", "su_password", "li_email", "li_password",
                "fo_email", "rp_pass", "rp_confirm"):
        st.session_state.pop(key, None)


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
    image_uri = T.asset_uri("farmwise-field")
    with st.container(key="signup-page"):
        left, right = st.columns([1, 1.2], gap=None, vertical_alignment="top")
        with left:
            T.show(
                f'<div class="fw-signup-image"><img src="{image_uri or ""}" alt="Farm field at sunrise"></div>',
                unsafe_allow_html=True,
            )
        with right:
            T.show(
                f"""
<div class="fw-signup-heading">{ui.logo()}
  <h1>Create your account</h1>
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
                    "Password", placeholder="Password", type="password",
                    label_visibility="collapsed", key="su_password",
                )
                create = st.form_submit_button("Create account", type="primary", width="stretch")
            T.show(
                '<p class="fw-small" style="text-align:center;margin:14px 0 4px">'
                f'Already have an account? <a href="{href("login")}" style="font-weight:600;color:var(--text)">Log in</a></p>',
                unsafe_allow_html=True,
            )
            if create:
                name, email = name.strip(), email.strip()
                if not name or not email or not password:
                    st.error("Please fill in your name, email and password.")
                else:
                    try:
                        with st.spinner("Creating your account..."):
                            payload = auth_api.signup(name, email, password)
                        st.session_state.pending_email = email
                        st.session_state.signup_notice = payload.get(
                            "message", "Check your email for a verification code."
                        )
                        _clear_otp_inputs()
                        go("verify")
                    except APIError as exc:
                        _show_api_error(exc)


# ------------------------------------------------------------------- verify email


def login() -> None:
    if st.session_state.pop("clear_auth_widgets", False):
        _clear_auth_widgets()
    auth_notice = st.session_state.pop("auth_notice", None)
    if auth_api.is_authenticated(st.session_state):
        go("dashboard")
        return
    if auth_notice:
        st.success(auth_notice)
    _frame()
    with st.container(key="authsplit"):
        left, right = st.columns([1, 1.2], gap="small")
        with left:
            T.show(
                f'<div class="fw-auth-art" style="{T.media("farmwise-farmer", 0, 0.12)}"></div>',
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
                    "Password", placeholder="Password", type="password",
                    label_visibility="collapsed", key="li_password",
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
                email = email.strip()
                st.session_state.pop("login_unverified_email", None)
                if not email or not password:
                    st.error("Enter your email and password to continue.")
                elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                    st.error("Enter a valid email address.")
                elif st.session_state.get("login_inflight"):
                    st.info("Login is already processing.")
                else:
                    st.session_state.login_inflight = True
                    profile = None
                    try:
                        with st.spinner("Logging in..."):
                            profile = auth_api.establish_session(email, password, st.session_state)
                    except APIError as exc:
                        if exc.error_code == "EMAIL_NOT_VERIFIED":
                            st.session_state.login_unverified_email = email
                        elif st.session_state.get("auth_pending_login_email"):
                            # Credentials were accepted; only profile loading needs retrying.
                            st.session_state.clear_auth_widgets = True
                        _show_api_error(exc)
                    finally:
                        st.session_state.pop("login_inflight", None)
                    if profile:
                        go("dashboard")

            unverified_email = st.session_state.get("login_unverified_email")
            if unverified_email:
                st.info("Verify your email before logging in. You can continue with the existing verification code.")
                if st.button("Verify email", key="login_verify_email"):
                    st.session_state.pending_email = unverified_email
                    st.session_state.clear_auth_widgets = True
                    go("verify")

            pending_profile_email = st.session_state.get("auth_pending_login_email")
            if pending_profile_email:
                st.info("Login succeeded, but the profile could not be loaded yet. Retry the profile check.")
                if st.button("Retry profile check", key="login_retry_profile"):
                    try:
                        with st.spinner("Loading your account..."):
                            auth_api.resume_login(st.session_state)
                        go("dashboard")
                    except APIError as exc:
                        _show_api_error(exc)


def require_authenticated(*, admin_only: bool = False) -> bool:
    session = st.session_state
    if not auth_api.can_access_private(session):
        st.warning("Log in to access this page.")
        go("login")
        return False
    if not auth_api.can_access_private(session, admin_only=admin_only):
        st.error("Your account does not have access to this page.")
        go("dashboard")
        return False
    # Drop the password widget value once the authenticated page is active.
    session.pop("li_password", None)
    return True


def account() -> None:
    if not require_authenticated():
        return
    try:
        with st.spinner("Loading your account..."):
            profile = auth_api.me(st.session_state)
    except APIError as exc:
        if not auth_api.is_authenticated(st.session_state):
            st.session_state.auth_notice = exc.message
            go("login")
            return
        _show_api_error(exc)
        if st.button("Retry profile", key="profile_retry"):
            st.rerun()
        return

    with st.container(key="authplain"):
        T.show(
            f"""
<div style="text-align:center">
  {ui.logo()}
  <h1 class="fw-auth-head" style="text-align:center;margin-top:26px">Your account</h1>
</div>
""",
            unsafe_allow_html=True,
        )
        rows = "".join(
            f'<div style="display:flex;justify-content:space-between;gap:16px;padding:12px 0;'
            f'border-bottom:1px solid var(--line);text-align:left">'
            f'<span style="color:var(--muted)">{html.escape(label)}</span>'
            f'<strong style="color:var(--text);text-align:right;overflow-wrap:anywhere">'
            f'{html.escape(str(value))}</strong></div>'
            for label, value in (
                ("ID", profile["id"]),
                ("Name", profile["name"]),
                ("Email", profile["email"]),
                ("Role", profile["role"]),
                ("Email verified", "Yes" if profile["email_verified"] else "No"),
            )
        )
        T.show(f'<div class="fw-profile-details">{rows}</div>', unsafe_allow_html=True)
        if st.button("Log out", type="primary", width="stretch", key="profile_logout"):
            try:
                with st.spinner("Logging out..."):
                    auth_api.logout_session(st.session_state)
                st.session_state.auth_notice = "You have been logged out."
                go("login")
            except APIError as exc:
                _show_api_error(exc)


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


# --------------------------------------------------------------- email OTP flow


def _masked_pending_email() -> str:
    name, separator, domain = str(st.session_state.get("pending_email", "")).partition("@")
    masked = f"{name[:1]}***@{domain}" if separator else "your email address"
    return html.escape(masked)


def _show_otp_brand(title: str, description: str) -> None:
    T.show(
        f"""
<div class="fw-otp-heading">
  {ui.logo()}
  <div class="fw-otp-mail">{T.icon("mail")}</div>
  <h1 class="fw-auth-head">{title}</h1>
  <p class="fw-small">{description}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def verify() -> None:
    if st.session_state.pop("clear_auth_widgets", False):
        _clear_auth_widgets()
    st.session_state.pop("su_password", None)
    pending_email = st.session_state.get("pending_email", "")
    if not pending_email:
        st.error("Start from the signup page to request an email verification code.")
        if st.button("Go to signup", key="verify_to_signup"):
            go("signup")
        return
    with st.container(key="otp-verify"):
        signup_notice = st.session_state.pop("signup_notice", None)
        if signup_notice:
            st.info(signup_notice)
        _show_otp_brand(
            "Verify your email",
            "Check your inbox or spam folder.<br>Enter the 6-digit code sent to "
            f"<strong>{_masked_pending_email()}</strong>.",
        )
        with st.container(key="otp-digits"):
            digit_columns = st.columns(6, gap="small")
            for index, column in enumerate(digit_columns):
                column.text_input(
                    f"Digit {index + 1}",
                    max_chars=6,
                    key=f"otp_{index}",
                    label_visibility="collapsed",
                    placeholder="",
                    on_change=_distribute_pasted_otp,
                )

        code = "".join(
            str(st.session_state.get(f"otp_{index}", "") or "")
            for index in range(6)
        )
        if st.button("Verify email", type="primary", width="stretch", key="verify_btn"):
            if len(code) != 6 or not code.isascii() or not code.isdigit():
                st.error("Enter the complete 6-digit verification code.")
            elif st.session_state.get("verify_inflight"):
                st.info("Verification is already processing.")
            else:
                st.session_state.verify_inflight = True
                try:
                    with st.spinner("Verifying your email..."):
                        auth_api.verify_email(pending_email, code)
                    st.session_state.pop("pending_email", None)
                    st.session_state.auth_notice = "Your email is verified. You can now log in."
                    go("login")
                except APIError as exc:
                    _show_api_error(exc)
                finally:
                    st.session_state.verify_inflight = False

        notice = st.session_state.pop("otp_notice", None)
        if notice:
            st.success(notice)
        T.show(
            '<p class="fw-small fw-otp-link">Didn\'t get a code? '
            f'<a href="{href("resend")}" target="_self">Resend code</a></p>',
            unsafe_allow_html=True,
        )


def resend() -> None:
    pending_email = st.session_state.get("pending_email", "")
    if not pending_email:
        st.error("There is no pending email verification. Start from the signup page.")
        if st.button("Go to signup", key="resend_to_signup"):
            go("signup")
        return
    with st.container(key="otp-resend"):
        _show_otp_brand(
            "Resend verification code",
            "We will send a new code to <strong>"
            f"{_masked_pending_email()}</strong>.",
        )
        with st.form("resend_form", border=False):
            send_code = st.form_submit_button("Send new code", type="primary", width="stretch")
        if send_code:
            if st.session_state.get("resend_inflight"):
                st.info("A resend request is already processing.")
            else:
                st.session_state.resend_inflight = True
                try:
                    with st.spinner("Sending a new code..."):
                        payload = auth_api.resend_verification(pending_email)
                    _clear_otp_inputs()
                    st.session_state.otp_notice = payload.get(
                        "message", "If the address can receive verification, instructions will be sent shortly."
                    )
                    go("verify")
                except APIError as exc:
                    _show_api_error(exc)
                finally:
                    st.session_state.resend_inflight = False
        if st.button("Back to verification", width="stretch", key="back_verify"):
            go("verify")
