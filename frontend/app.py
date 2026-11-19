import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="FarmWiseAI Admin", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS STYLING (Exact Match to Image) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f7f8fa; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #151b18 !important;
        width: 260px !important;
        padding-top: 20px;
    }
    [data-testid="stSidebar"] * { color: #d1d5db; }
    
    /* Sidebar Logo */
    .sidebar-logo {
        font-size: 22px; font-weight: 700; color: #ffffff;
        display: flex; align-items: center; gap: 8px; margin-bottom: 30px; padding-left: 15px;
    }
    .sidebar-logo span { color: #a3e635; }
    
    /* Sidebar Admin Label */
    .admin-label { font-size: 11px; font-weight: 600; color: #6b7280; margin-bottom: 10px; padding-left: 15px; letter-spacing: 1px; }

    /* Sidebar Navigation Buttons (Hide default radio circles) */
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label {
        padding: 10px 15px; border-radius: 8px; margin-bottom: 4px; 
        cursor: pointer; transition: 0.2s; width: 90%; margin-left: 5%;
    }
    div[role="radiogroup"] > label:hover { background-color: #2a332e; }
    /* Active state styling */
    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #a3e635 !important; color: #000 !important; font-weight: 600;
    }
    div[role="radiogroup"] > label[data-checked="true"] * { color: #000 !important; }

    /* Sidebar User Profile */
    .user-profile {
        display: flex; align-items: center; gap: 10px; background-color: #1f2924;
        padding: 12px; border-radius: 12px; margin-top: 50px; margin-bottom: 10px;
    }
    .user-avatar {
        background-color: #a3e635; color: #000; font-weight: bold; width: 35px; height: 35px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
    }
    
    /* Main Content Headers */
    h1, h2, h3 { color: #111827; font-family: 'Inter', sans-serif; }
    .sub-text { color: #6b7280; font-size: 15px; margin-bottom: 30px; }
    
    /* Custom Metric Cards */
    .metric-card-dark {
        background-color: #23372e; color: white; padding: 24px;
        border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-card-light {
        background-color: white; color: #111827; padding: 24px;
        border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e5e7eb;
    }
    .metric-value { font-size: 40px; font-weight: 700; margin-top: 10px; }
    
    /* Table Badges */
    .badge-green { background-color: #e2f5cb; color: #3f6212; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; }
    .badge-dark { background-color: #23372e; color: white; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; }
    .badge-gray { background-color: #e5e7eb; color: #4b5563; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; }
    
    /* Input fields and Buttons */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: white; border: 1px solid #d1d5db; border-radius: 8px;
    }
    .stButton>button {
        background-color: #e2f5cb; color: #3f6212; border: 1px solid #a3e635;
        border-radius: 8px; font-weight: 600; padding: 8px 16px; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #a3e635; color: #000; border-color: #a3e635; }
    
    /* Hide Streamlit default header and footer */
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Custom Table Styling */
    .custom-table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .custom-table th { text-align: left; padding: 15px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 13px; font-weight: 600; }
    .custom-table td { padding: 15px; border-bottom: 1px solid #f3f4f6; font-size: 14px; color: #111827; }
    .custom-table tr:last-child td { border-bottom: none; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo"><span>🌿</span> FarmWiseAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="admin-label">ADMIN</div>', unsafe_allow_html=True)
    
    # Hidden radio for state, styled via CSS
    page = st.radio("Navigation", ["🏠 Overview", "👥 Users & roles", "🧾 Audit activity", "⚙️ Settings"], label_visibility="collapsed")
    
    # Sidebar Footer Profile
    st.markdown("""
    <div class="user-profile">
        <div class="user-avatar">A</div>
        <div>
            <div style="font-size:14px; font-weight:600; color:#fff;">Admin</div>
            <div style="font-size:12px; color:#9ca3af;">Platform admin</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- PAGE 1: OVERVIEW ---
if page == "🏠 Overview":
    st.markdown("Welcome back", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top:-10px;'>Admin overview</h1>", unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Manage users, access and activity for FarmWiseAI.</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card-dark'>
            <div style='font-size: 24px;'>👥</div>
            <div style='font-size: 14px; margin-top:10px; color:#a3e635;'>Total users</div>
            <div class='metric-value'>68</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card-light'>
            <div style='font-size: 24px;'>👤</div>
            <div style='font-size: 14px; margin-top:10px; color:#6b7280;'>Active accounts</div>
            <div class='metric-value'>64</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card-light'>
            <div style='font-size: 24px;'>💬</div>
            <div style='font-size: 14px; margin-top:10px; color:#6b7280;'>Questions</div>
            <div class='metric-value'>5,420</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    st.write("")
    
    # Recent Activity Header & Button
    col_h, col_b = st.columns([3, 1])
    with col_h:
        st.markdown("### Recent activity")
        st.markdown('<div class="sub-text" style="margin-top:-15px;">Latest admin and user actions on the platform.</div>', unsafe_allow_html=True)
    with col_b:
        st.button("View audit log →", use_container_width=True)

    # Custom HTML Table for Recent Activity
    st.markdown("""
    <table class="custom-table">
        <tr><th>Time</th><th>Actor</th><th>Action</th><th>Details</th></tr>
        <tr><td>Today, 10:24 AM</td><td><span class="badge-green">AR</span> Arun Rao</td><td>User updated</td><td>Changed role to Admin</td></tr>
        <tr><td>Today, 09:56 AM</td><td><span class="badge-green">MS</span> Meera Singh</td><td>Account disabled</td><td>Disabled user account</td></tr>
        <tr><td>Today, 09:18 AM</td><td><span class="badge-green">KV</span> Kiran Verma</td><td>User invited</td><td>Invited kiran@farmwise.ai</td></tr>
        <tr><td>Yesterday, 05:42 PM</td><td><span class="badge-green">DP</span> Divya Patil</td><td>Settings changed</td><td>Updated RAG data sources</td></tr>
        <tr><td>Yesterday, 03:07 PM</td><td><span class="badge-green">AR</span> Arun Rao</td><td>Account enabled</td><td>Re-enabled user account</td></tr>
    </table>
    """, unsafe_allow_html=True)

# --- PAGE 2: USERS & ROLES ---
elif page == "👥 Users & roles":
    col_top1, col_top2 = st.columns([4, 1])
    with col_top1:
        st.markdown("<h1>Users & roles</h1>", unsafe_allow_html=True)
        st.markdown('<div class="sub-text">Manage user accounts, roles and access.</div>', unsafe_allow_html=True)
    with col_top2:
        st.write("")
        st.button("+ Add user", use_container_width=True)
    
    # Filters
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.text_input("Search users by name or email", placeholder="🔍 Search...", label_visibility="collapsed")
    with c2: st.selectbox("Role", ["All", "Admin", "User"], label_visibility="collapsed")
    with c3: st.selectbox("Status", ["All", "Active", "Disabled"], label_visibility="collapsed")
    
    st.write("")
    
    # Custom Table for Users
    st.markdown("""
    <table class="custom-table">
        <tr><th>User</th><th>Role</th><th>Status</th><th>Actions</th></tr>
        <tr>
            <td><div style="display:flex; align-items:center; gap:10px;"><span class="badge-green">AR</span><div><b>Arun Rao</b><br><span style="color:#6b7280; font-size:12px;">arun@farmwise.ai</span></div></div></td>
            <td><span class="badge-dark">Admin</span></td>
            <td><span class="badge-green">Active</span></td>
            <td>⋮</td>
        </tr>
        <tr>
            <td><div style="display:flex; align-items:center; gap:10px;"><span class="badge-green">MS</span><div><b>Meera Singh</b><br><span style="color:#6b7280; font-size:12px;">meera@farmwise.ai</span></div></div></td>
            <td><span class="badge-gray">User</span></td>
            <td><span class="badge-green">Active</span></td>
            <td>⋮</td>
        </tr>
        <tr>
            <td><div style="display:flex; align-items:center; gap:10px;"><span class="badge-green">KV</span><div><b>Kiran Verma</b><br><span style="color:#6b7280; font-size:12px;">kiran@farmwise.ai</span></div></div></td>
            <td><span class="badge-gray">User</span></td>
            <td><span class="badge-gray">Disabled</span></td>
            <td>⋮</td>
        </tr>
        <tr>
            <td><div style="display:flex; align-items:center; gap:10px;"><span class="badge-green">DP</span><div><b>Divya Patil</b><br><span style="color:#6b7280; font-size:12px;">divya@farmwise.ai</span></div></div></td>
            <td><span class="badge-dark">Admin</span></td>
            <td><span class="badge-green">Active</span></td>
            <td>⋮</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

# --- PAGE 3: AUDIT ACTIVITY ---
elif page == "🧾 Audit activity":
    st.markdown("<h1>Audit activity</h1>", unsafe_allow_html=True)
    st.markdown('<div class="sub-text">A record of key actions and changes in the account.</div>', unsafe_allow_html=True)
    
    # Filters
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.text_input("Search", placeholder="🔍 Search actions, users or details", label_visibility="collapsed")
    with c2: st.selectbox("Action", ["All", "User updated", "Account disabled"], label_visibility="collapsed")
    with c3: st.selectbox("Time", ["Last 7 days", "Last 30 days"], label_visibility="collapsed")
    
    st.write("")
    
    # Custom Table
    st.markdown("""
    <table class="custom-table">
        <tr><th>Time</th><th>Actor</th><th>Action</th><th>Details</th></tr>
        <tr><td>Today, 10:24 AM</td><td><span class="badge-green">AR</span> Arun Rao</td><td>User updated</td><td>Changed role to Admin</td></tr>
        <tr><td>Today, 09:56 AM</td><td><span class="badge-green">MS</span> Meera Singh</td><td>Account disabled</td><td>Disabled user account</td></tr>
        <tr><td>Today, 09:18 AM</td><td><span class="badge-green">KV</span> Kiran Verma</td><td>User invited</td><td>Invited kiran@farmwise.ai</td></tr>
    </table>
    """, unsafe_allow_html=True)

    # The Modal / Popup (Using Streamlit's expander to simulate it visually)
    st.write("")
    st.write("")
    with st.expander("⚠️ View Disable Account Popup (Click to Open)", expanded=False):
        st.warning("This will prevent Meera Singh from signing in and using FarmWiseAI.")
        c1, c2, _ = st.columns([1,1,3])
        with c1: st.button("Cancel", use_container_width=True)
        with c2: st.button("Disable account", use_container_width=True, type="primary")

# --- PAGE 4: SETTINGS ---
elif page == "⚙️ Settings":
    st.markdown("<h1>Settings</h1>", unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Manage your platform preferences and configurations.</div>', unsafe_allow_html=True)
    
    st.info("Settings panel placeholder. Add your configuration fields here.")