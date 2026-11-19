"""Admin console: overview, users & roles, audit activity, settings."""

from __future__ import annotations

import streamlit as st

from farmwise import components as ui
from farmwise import state as app_state
from farmwise import theme as T
from farmwise.data import RAG_SOURCES
from farmwise.routes import go

NAV = [
    ("admin", "Overview", ":material/home:"),
    ("admin_users", "Users & roles", ":material/group:"),
    ("admin_audit", "Audit activity", ":material/layers:"),
    ("admin_settings", "Settings", ":material/settings:"),
]


def _find(email: str) -> dict | None:
    return next((u for u in st.session_state.users if u["email"] == email), None)


def _set_status(email: str, status: str) -> None:
    user = _find(email)
    if not user:
        return
    user["status"] = status
    verb = "Account enabled" if status == "Active" else "Account disabled"
    detail = "Re-enabled user account" if status == "Active" else "Disabled user account"
    app_state.log(verb, f"{detail} · {email}")


def _toggle_role(email: str) -> None:
    user = _find(email)
    if not user:
        return
    user["role"] = "User" if user["role"] == "Admin" else "Admin"
    app_state.log("User updated", f"Changed role to {user['role']} · {email}")


def _delete(email: str) -> None:
    st.session_state.users = [u for u in st.session_state.users if u["email"] != email]
    app_state.log("User deleted", f"Removed {email}")


@st.dialog("Disable account?")
def _confirm_disable(email: str) -> None:
    user = _find(email)
    if not user:
        st.rerun()
    T.show(f"This will prevent **{user['name']}** from signing in and using FarmWiseAI.")
    left, right = st.columns(2)
    if left.button("Cancel", width="stretch"):
        st.rerun()
    if right.button("Disable account", type="primary", width="stretch"):
        _set_status(email, "Disabled")
        st.rerun()


@st.dialog("Delete account?")
def _confirm_delete(email: str) -> None:
    user = _find(email)
    if not user:
        st.rerun()
    T.show(f"**{user['name']}** will lose access permanently. This cannot be undone.")
    left, right = st.columns(2)
    if left.button("Cancel", key="del_cancel", width="stretch"):
        st.rerun()
    if right.button("Delete user", key="del_ok", type="primary", width="stretch"):
        _delete(email)
        st.rerun()


def _sidebar(active: str) -> None:
    with st.sidebar:
        with st.container(key="adminbrand"):
            T.show(ui.logo(light=True, size="16px"), unsafe_allow_html=True)
            T.show('<p style="margin-top:12px">ADMIN</p>', unsafe_allow_html=True)
        for slug, label, icon in NAV:
            if st.button(
                label,
                key=f"adm_{slug}",
                icon=icon,
                width="stretch",
                type="primary" if active == slug else "secondary",
            ):
                go(slug)
        st.write("")
        T.show(
            f"""
<div class="fw-who" style="padding:12px 4px 0">
  <span class="fw-av" style="background:var(--lime);color:#12211A">A</span>
  <div>
    <strong style="color:#fff;font-size:13.5px">Admin</strong>
    <small style="color:rgba(255,255,255,.62)">Platform admin</small>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="adm_signout", icon=":material/logout:", width="stretch"):
            go("home")


def _table(headers: list[str], rows: list[str]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    return (
        f'<div class="fw-tablecard"><table class="fw-tbl"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def _audit_rows(events: list[dict]) -> list[str]:
    return [
        f"""
<tr>
  <td style="white-space:nowrap;color:var(--muted)">{e["time"]}</td>
  <td>{ui.who(e["actor"])}</td>
  <td style="font-weight:500">{e["action"]}</td>
  <td style="color:var(--muted)">{e["details"]}</td>
</tr>"""
        for e in events
    ]


# ------------------------------------------------------------------- overview


def overview() -> None:
    app_state.init()
    _sidebar("admin")
    users = st.session_state.users
    total = len(users)
    active = sum(1 for u in users if u["status"] == "Active")

    with st.container(key="adminframe"):
        T.show(
            """
<div class="fw-eyebrow" style="margin-bottom:4px">Welcome back</div>
<h1 class="fw-admin-title">Admin overview</h1>
<p class="fw-admin-sub">Manage users, access and activity for FarmWiseAI.</p>
""",
            unsafe_allow_html=True,
        )
        cols = st.columns(3, gap="medium")
        cols[0].markdown(ui.stat_card("users", "Total users", str(total), dark=True), unsafe_allow_html=True)
        cols[1].markdown(ui.stat_card("user", "Active accounts", str(active)), unsafe_allow_html=True)
        cols[2].markdown(ui.stat_card("send", "Questions", "5,420"), unsafe_allow_html=True)

        st.write("")
        head = st.columns([3, 1], vertical_alignment="center")
        head[0].markdown(
            """
<h2 class="fw-h3" style="font-size:21px">Recent activity</h2>
<p class="fw-small" style="margin-top:4px">Latest admin and user actions on the platform.</p>
""",
            unsafe_allow_html=True,
        )
        with head[1]:
            if st.button(
                "View audit log",
                key="view_audit",
                type="primary",
                icon=":material/arrow_forward:",
            ):
                go("admin_audit")

        T.show(
            _table(["Time", "Actor", "Action", "Details"], _audit_rows(st.session_state.audit[:5])),
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------- users


def users() -> None:
    app_state.init()
    _sidebar("admin_users")

    with st.container(key="adminframe"):
        head = st.columns([3, 1], vertical_alignment="center")
        head[0].markdown(
            """
<h1 class="fw-admin-title">Users & roles</h1>
<p class="fw-admin-sub">Manage user accounts, roles and access.</p>
""",
            unsafe_allow_html=True,
        )
        with head[1]:
            with st.container(key="adduser"):
                with st.popover("Add user", icon=":material/add:"):
                    with st.form("add_user_form"):
                        name = st.text_input("Full name", placeholder="e.g. Ayesha Malik", key="au_name")
                        email = st.text_input("Email", placeholder="name@farmwise.ai", key="au_email")
                        role = st.selectbox("Role", ["User", "Admin"], key="au_role")
                        created = st.form_submit_button("Create account", type="primary", width="stretch")
                    if created:
                        if not name or not email:
                            st.error("Name and email are required.")
                        else:
                            st.session_state.users.append(
                                {"name": name, "email": email, "role": role, "status": "Active"}
                            )
                            app_state.log("User invited", f"Invited {email}")
                            st.rerun()

        with st.container(key="adminfilter"):
            filters = st.columns([2.4, 1, 1], gap="small")
            query = filters[0].text_input(
                "Search users",
                placeholder="Search users by name or email",
                label_visibility="collapsed",
                key="user_query",
            )
            role_filter = filters[1].selectbox(
                "Role", ["All roles", "Admin", "User"], label_visibility="collapsed", key="role_filter"
            )
            status_filter = filters[2].selectbox(
                "Status",
                ["All statuses", "Active", "Disabled"],
                label_visibility="collapsed",
                key="status_filter",
            )

        rows = [
            u
            for u in st.session_state.users
            if (not query or query.lower() in u["name"].lower() or query.lower() in u["email"].lower())
            and (role_filter == "All roles" or u["role"] == role_filter)
            and (status_filter == "All statuses" or u["status"] == status_filter)
        ]

        widths = [3, 1.25, 1.2, 0.6]
        labels = st.columns(widths, gap="small")
        for column, text in zip(labels, ["User", "Role", "Status", "Actions"]):
            column.markdown(
                f'<div class="fw-mini-label" style="margin:6px 0 4px">{text}</div>', unsafe_allow_html=True
            )

        for index, user in enumerate(rows):
            with st.container(key=f"urow_{index}"):
                cells = st.columns(widths, gap="small", vertical_alignment="center")
                cells[0].markdown(ui.who(user["name"], user["email"]), unsafe_allow_html=True)
                cells[1].markdown(
                    ui.badge(
                        user["role"],
                        "solid" if user["role"] == "Admin" else "outline",
                    ),
                    unsafe_allow_html=True,
                )
                cells[2].markdown(
                    ui.badge(user["status"], "lime" if user["status"] == "Active" else "muted"),
                    unsafe_allow_html=True,
                )
                with cells[3]:
                    with st.popover("⋮"):
                        st.caption(user["email"])
                        if st.button("Edit user", key=f"edit_{index}", icon=":material/edit:", width="stretch"):
                            st.toast(f"Opened profile for {user['name']}")
                        st.button(
                            "Make user" if user["role"] == "Admin" else "Make admin",
                            key=f"role_{index}",
                            icon=":material/swap_horiz:",
                            width="stretch",
                            on_click=_toggle_role,
                            args=(user["email"],),
                        )
                        if user["status"] == "Active":
                            if st.button(
                                "Disable account",
                                key=f"dis_{index}",
                                icon=":material/block:",
                                width="stretch",
                            ):
                                _confirm_disable(user["email"])
                        else:
                            if st.button(
                                "Enable account",
                                key=f"ena_{index}",
                                icon=":material/check_circle:",
                                width="stretch",
                            ):
                                _set_status(user["email"], "Active")
                                st.rerun()
                        if st.button(
                            "Delete", key=f"del_{index}", icon=":material/delete:", width="stretch"
                        ):
                            _confirm_delete(user["email"])

        st.caption(f"{len(rows)} of {len(st.session_state.users)} accounts")


# ---------------------------------------------------------------------- audit


def audit() -> None:
    app_state.init()
    _sidebar("admin_audit")

    with st.container(key="adminframe"):
        T.show(
            """
<h1 class="fw-admin-title">Audit activity</h1>
<p class="fw-admin-sub">A record of key actions and changes in the account.</p>
""",
            unsafe_allow_html=True,
        )

        with st.container(key="adminfilter"):
            filters = st.columns([2.6, 1, 1], gap="small")
            query = filters[0].text_input(
                "Search actions",
                placeholder="Search actions, users or details",
                label_visibility="collapsed",
                key="audit_query",
            )
            action = filters[1].selectbox(
                "Action",
                ["Action: All", "User updated", "Account disabled", "Account enabled", "User invited", "Settings changed"],
                label_visibility="collapsed",
                key="audit_action",
            )
            window = filters[2].selectbox(
                "Range", ["Last 7 days", "Last 30 days", "All time"], label_visibility="collapsed", key="audit_window"
            )

        events = [
            e
            for e in st.session_state.audit
            if (
                not query
                or query.lower() in f"{e['actor']} {e['action']} {e['details']}".lower()
            )
            and (action == "Action: All" or e["action"] == action)
        ]

        T.show(
            _table(["Time", "Actor", "Action", "Details"], _audit_rows(events)),
            unsafe_allow_html=True,
        )
        st.caption(f"{len(events)} events · {window}")


# -------------------------------------------------------------------- settings


def settings() -> None:
    app_state.init()
    _sidebar("admin_settings")

    with st.container(key="adminframe"):
        T.show(
            """
<h1 class="fw-admin-title">Settings</h1>
<p class="fw-admin-sub">Platform limits, access rules and knowledge sources.</p>
""",
            unsafe_allow_html=True,
        )

        left, right = st.columns(2, gap="medium")
        with left:
            T.show('<div class="fw-panel-title">Assistant limits</div>', unsafe_allow_html=True)
            st.number_input(
                "Questions per user / day", min_value=5, max_value=500, value=50, step=5, key="set_limit"
            )
            st.selectbox("Default answer language", ["English", "اردو (Urdu)"], key="set_lang")
            st.text_input("Support email", value="support@farmwise.ai", key="set_support")
        with right:
            T.show('<div class="fw-panel-title">Access rules</div>', unsafe_allow_html=True)
            st.toggle("Require email verification", value=True, key="set_verify")
            st.toggle("Allow role changes by admins", value=True, key="set_roles")
            st.toggle("Restrict new signups to invited emails", value=False, key="set_invite")

        st.write("")
        st.button("Save changes", key="save_settings", type="primary", icon=":material/save:")

        st.write("")
        T.show('<div class="fw-panel-title" style="margin-top:8px">Knowledge sources</div>', unsafe_allow_html=True)
        source_rows = [
            f"""
<tr>
  <td>{ui.who(s["name"], f'{s["docs"]} document')}</td>
  <td style="color:var(--muted)">{s["chunks"]} chunks</td>
  <td>{ui.badge(s["status"], "lime" if s["status"] == "Indexed" else "muted")}</td>
</tr>"""
            for s in RAG_SOURCES
        ]
        T.show(_table(["Source", "Size", "Status"], source_rows), unsafe_allow_html=True)
