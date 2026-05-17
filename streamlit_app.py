"""
ServicePro OS — Main Entry Point
Login, registration, and the authenticated navigation hub.
"""

import streamlit as st
import time

from utils.auth import (
    check_authentication,
    login_user,
    logout_user,
    hash_password,
    verify_password,
)
from utils.db import (
    get_user_by_email,
    create_user,
    get_company,
    create_company,
    get_supabase,
    SCHEMA_SQL,
    get_dashboard_stats,
)
from utils.styles import inject_css, render_metric_card, format_currency, COLORS

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ServicePro OS",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# ── Sidebar Brand Helper ───────────────────────────────────────────────────────

def _render_sidebar_brand():
    st.sidebar.markdown(
        """
        <div style="text-align:center; padding: 1rem 0;">
            <span style="font-size:2rem;">🔧</span>
            <div style="font-size:1.3rem; font-weight:800; color:#10B981;">ServicePro OS</div>
            <div style="font-size:0.7rem; color:#6B7280;">Field Operations Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Authenticated Sidebar Navigation ──────────────────────────────────────────

def _render_sidebar_nav():
    _render_sidebar_brand()

    user = st.session_state.get("user", {})
    company = st.session_state.get("company", {})

    # User info block
    role = user.get("role", "crew").title()
    st.sidebar.markdown(
        f"""
        <div style="padding:0.75rem; background:#F0FDF4; border-radius:10px; margin-bottom:1rem;">
            <div style="font-weight:700; color:#1F2937;">{user.get('name', 'User')}</div>
            <div style="font-size:0.75rem; color:#10B981; font-weight:600;">{role}</div>
            <div style="font-size:0.75rem; color:#6B7280;">{company.get('name', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("**Navigation**")

    nav_items = [
        ("📊", "Dashboard", "streamlit_app"),
        ("👥", "Clients", "pages/clients"),
        ("📝", "Estimates", "pages/estimates"),
        ("🔨", "Jobs", "pages/jobs"),
        ("👷", "Crew", "pages/crew"),
        ("📅", "Scheduling", "pages/scheduling"),
        ("💳", "Payments", "pages/payments"),
        ("💬", "Messages", "pages/messages"),
        ("🤖", "AI Assistant", "pages/ai_assistant"),
        ("⚙️", "Settings", "pages/settings"),
    ]

    for icon, label, page in nav_items:
        try:
            st.sidebar.page_link(f"{page}.py", label=f"{icon} {label}")
        except Exception:
            # Fallback if page doesn't exist yet
            st.sidebar.markdown(
                f'<div style="padding:0.4rem 0; color:#6B7280; font-size:0.9rem;">{icon} {label}</div>',
                unsafe_allow_html=True,
            )

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        logout_user()


# ── Login / Register Page ──────────────────────────────────────────────────────

def _render_login_page():
    _render_sidebar_brand()

    # Centered login card
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # Hero section
        st.markdown(
            """
            <div style="text-align:center; padding:2rem 0 1rem 0;">
                <div style="font-size:3.5rem;">🔧</div>
                <div style="font-size:2rem; font-weight:800; color:#10B981; margin-top:0.5rem;">
                    ServicePro OS
                </div>
                <div style="font-size:1rem; color:#6B7280; margin-top:0.25rem;">
                    The Operating System for Field Service Businesses
                </div>
                <div style="margin-top:0.75rem; display:flex; justify-content:center; gap:1rem; flex-wrap:wrap;">
                    <span style="background:#D1FAE5; color:#065F46; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:600;">🎨 Painting</span>
                    <span style="background:#DBEAFE; color:#1E40AF; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:600;">⚡ Electrical</span>
                    <span style="background:#FEF3C7; color:#92400E; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:600;">🌿 Landscaping</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_signin, tab_register = st.tabs(["Sign In", "Get Started"])

        # ── Sign In Tab ──────────────────────────────────────────────────────
        with tab_signin:
            st.markdown("#### Welcome back")
            email = st.text_input("Email", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

            if st.button("Sign In", key="btn_signin", use_container_width=True):
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    with st.spinner("Signing in..."):
                        user = get_user_by_email(email.strip().lower())
                        if user and verify_password(password, user.get("password_hash", "")):
                            company = get_company(user.get("company_id", ""))
                            if not company:
                                st.error("Company account not found. Please contact your administrator.")
                            else:
                                login_user(user, company)
                                st.rerun()
                        else:
                            st.error("Invalid email or password. Please try again.")

            st.markdown(
                """
                <div style="text-align:center; margin-top:1rem; font-size:0.8rem; color:#9CA3AF;">
                    Don't have an account? Use the <strong>Get Started</strong> tab above.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Get Started (Register) Tab ────────────────────────────────────────
        with tab_register:
            st.markdown("#### Create your account")

            company_name = st.text_input("Company Name", key="reg_company", placeholder="Acme Painting & Electric")
            your_name = st.text_input("Your Name", key="reg_name", placeholder="Jane Smith")
            reg_email = st.text_input("Email", key="reg_email", placeholder="jane@acme.com")
            reg_password = st.text_input("Password", type="password", key="reg_password", placeholder="Minimum 8 characters")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Repeat password")
            reg_role = st.selectbox(
                "Your Role",
                options=["owner", "admin", "estimator", "crew_lead"],
                format_func=lambda r: r.replace("_", " ").title(),
                key="reg_role",
            )

            if st.button("Create Account", key="btn_register", use_container_width=True):
                errors = []
                if not company_name.strip():
                    errors.append("Company name is required.")
                if not your_name.strip():
                    errors.append("Your name is required.")
                if not reg_email.strip():
                    errors.append("Email is required.")
                if len(reg_password) < 8:
                    errors.append("Password must be at least 8 characters.")
                if reg_password != reg_confirm:
                    errors.append("Passwords do not match.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    with st.spinner("Creating your account..."):
                        # Check if email already in use
                        existing = get_user_by_email(reg_email.strip().lower())
                        if existing:
                            st.error("An account with this email already exists. Please sign in.")
                        else:
                            # Create company first
                            new_company = create_company({"name": company_name.strip()})
                            if not new_company:
                                st.error(
                                    "Failed to create company account. "
                                    "Please check your Supabase configuration and try again."
                                )
                            else:
                                # Create user
                                new_user = create_user(
                                    {
                                        "company_id": new_company["id"],
                                        "name": your_name.strip(),
                                        "email": reg_email.strip().lower(),
                                        "password": reg_password,
                                        "role": reg_role,
                                    }
                                )
                                if not new_user:
                                    st.error(
                                        "Failed to create user account. "
                                        "Please try again or contact support."
                                    )
                                else:
                                    st.success(
                                        f"Account created! Welcome to ServicePro OS, {your_name.strip()}. "
                                        "Please sign in using the Sign In tab."
                                    )

    # Supabase setup notice when DB is not connected
    if get_supabase() is None:
        st.markdown("---")
        with st.expander("⚠️ Database Setup Required — Click to expand setup instructions", expanded=True):
            st.markdown(
                """
                ### Database Setup Required

                ServicePro OS uses **Supabase** as its database. Follow these steps to set it up:

                **Step 1:** Create a free project at [supabase.com](https://supabase.com)

                **Step 2:** In your Supabase project, go to **Project Settings → API** and copy:
                - **Project URL** (e.g. `https://xxxxx.supabase.co`)
                - **Service Role Key** (under "Project API keys")

                **Step 3:** In **Streamlit Cloud → App Settings → Secrets**, add:
                ```toml
                SUPABASE_URL = "https://xxxxx.supabase.co"
                SUPABASE_KEY = "your-service-role-key"
                ```

                **Step 4:** In Supabase, go to **SQL Editor** and run the schema below.

                **Step 5:** Restart this app.
                """
            )
            st.code(SCHEMA_SQL, language="sql")


# ── Authenticated Dashboard ────────────────────────────────────────────────────

def _render_dashboard():
    _render_sidebar_nav()

    user = st.session_state.get("user", {})
    company = st.session_state.get("company", {})

    # Page header
    st.markdown(
        f"""
        <div class="page-header">
            <h1>Welcome back, {user.get('name', 'there')}! 👋</h1>
            <p>{company.get('name', 'ServicePro OS')} — Field Operations Dashboard</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Database not configured notice
    if get_supabase() is None:
        st.warning(
            "**Database not connected.** ServicePro OS needs Supabase to store data. "
            "Please follow the setup instructions on the login page."
        )
        with st.expander("View Database Setup Instructions"):
            st.markdown(
                """
                1. Create a free Supabase project at [supabase.com](https://supabase.com)
                2. Copy your **Project URL** and **Service Role Key**
                3. In Streamlit Cloud Settings → Secrets, add:
                ```toml
                SUPABASE_URL = "https://xxx.supabase.co"
                SUPABASE_KEY = "your-service-role-key"
                ```
                4. Run this SQL in the Supabase SQL editor:
                """
            )
            st.code(SCHEMA_SQL, language="sql")
            st.markdown("5. Restart this app.")
        return

    # Load dashboard stats
    with st.spinner("Loading dashboard..."):
        company_id = company.get("id", "")
        stats = get_dashboard_stats(company_id) if company_id else {}

    # Key metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            render_metric_card(
                "Total Clients",
                stats.get("total_clients", 0),
                icon="👥",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            render_metric_card(
                "Active Jobs",
                stats.get("active_jobs", 0),
                icon="🔨",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            render_metric_card(
                "Open Estimates",
                stats.get("open_estimates", 0),
                icon="📝",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            render_metric_card(
                "Total Revenue",
                format_currency(stats.get("total_revenue", 0)),
                icon="💰",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Second row
    c5, c6 = st.columns(2)
    with c5:
        st.markdown(
            render_metric_card(
                "Jobs This Month",
                stats.get("jobs_this_month", 0),
                icon="📅",
            ),
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            render_metric_card(
                "Revenue This Month",
                format_currency(stats.get("revenue_this_month", 0)),
                icon="📈",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent activity
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### Recent Activity")
        activity = stats.get("recent_activity", [])
        if activity:
            for item in activity:
                icon = "🔨" if item.get("type") == "job" else "📝"
                time_str = item.get("time", "")[:10] if item.get("time") else ""
                st.markdown(
                    f"""
                    <div class="card" style="margin-bottom:0.5rem; padding:0.75rem 1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-size:1.1rem;">{icon}</span>
                                <strong style="margin-left:8px;">{item.get('title', '')}</strong>
                                <span style="color:#6B7280; font-size:0.85rem; margin-left:8px;">{item.get('detail', '')}</span>
                            </div>
                            <div style="color:#9CA3AF; font-size:0.8rem;">{time_str}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div style="text-align:center; padding:2rem; color:#9CA3AF;">
                    <div style="font-size:2rem;">📋</div>
                    <div style="margin-top:0.5rem;">No activity yet — create your first client or estimate to get started.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_right:
        st.markdown("### Quick Actions")
        actions = [
            ("➕ New Client", "pages/clients.py"),
            ("📝 New Estimate", "pages/estimates.py"),
            ("🔨 New Job", "pages/jobs.py"),
            ("📅 Schedule Work", "pages/scheduling.py"),
            ("💬 Messages", "pages/messages.py"),
            ("🤖 Ask AI Assistant", "pages/ai_assistant.py"),
        ]
        for label, page in actions:
            try:
                st.page_link(page, label=label)
            except Exception:
                st.markdown(
                    f'<div style="padding:0.3rem 0; color:#10B981; font-size:0.9rem;">{label}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("### API Configuration")

        has_stripe = bool(company.get("stripe_secret_key"))
        has_gmail = bool(company.get("gmail_email") and company.get("gmail_app_password"))
        has_maps = bool(company.get("google_maps_key"))
        has_ai = bool(company.get("anthropic_key"))

        integrations = [
            ("💳 Stripe Payments", has_stripe),
            ("📧 Gmail Integration", has_gmail),
            ("🗺️ Google Maps", has_maps),
            ("🤖 AI Assistant", has_ai),
        ]

        for name, configured in integrations:
            status_icon = "✅" if configured else "⚠️"
            status_text = "Configured" if configured else "Not set"
            status_color = "#10B981" if configured else "#F59E0B"
            st.markdown(
                f'<div style="display:flex; justify-content:space-between; padding:4px 0; font-size:0.85rem;">'
                f'<span>{name}</span>'
                f'<span style="color:{status_color}; font-weight:600;">{status_icon} {status_text}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div style="margin-top:0.5rem;">', unsafe_allow_html=True
        )
        try:
            st.page_link("pages/settings.py", label="⚙️ Configure Integrations")
        except Exception:
            st.markdown("⚙️ Go to Settings to configure integrations", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ── Main Entry Point ───────────────────────────────────────────────────────────

def main():
    if check_authentication():
        _render_dashboard()
    else:
        _render_login_page()


main()
