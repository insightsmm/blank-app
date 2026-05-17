import streamlit as st
from datetime import datetime

from utils.auth import check_authentication, is_role
from utils.styles import (
    inject_css,
    render_metric_card,
    render_badge,
    render_page_header,
    format_currency,
    format_date,
    COLORS,
)
from utils.db import (
    get_dashboard_stats,
    get_jobs,
    get_estimates,
    get_clients,
    get_notifications,
    get_unread_notifications_count,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard | ServicePro OS",
    page_icon="📊",
    layout="wide",
)

# ── Auth guard ───────────────────────────────────────────────────────────────
if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()

# ── Convenience vars ─────────────────────────────────────────────────────────
user = st.session_state.user
company = st.session_state.company
role = st.session_state.role
company_id = company["id"]
user_id = user["id"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">⚡ ServicePro OS</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="margin-bottom:0.5rem;">
            <div style="font-weight:700;font-size:1rem;color:#1F2937;">{company.get('name','My Company')}</div>
            <div style="font-size:0.85rem;color:#6B7280;">{user.get('name','')}</div>
            <div style="margin-top:4px;">{render_badge(role)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Notification count
    try:
        unread = get_unread_notifications_count(user_id)
        if unread > 0:
            st.markdown(
                f'<div style="background:#FEF3C7;color:#92400E;padding:6px 12px;'
                f'border-radius:8px;font-size:0.85rem;font-weight:600;margin-top:8px;">'
                f'🔔 {unread} unread notification{"s" if unread != 1 else ""}</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    st.markdown("---")
    st.markdown("**Navigation**")
    st.page_link("pages/1_Dashboard.py", label="📊 Dashboard")
    st.page_link("pages/2_Clients.py", label="👥 Clients")
    st.page_link("pages/3_Estimates.py", label="📝 Estimates")

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header("📊 Dashboard", "Your business at a glance")

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading dashboard..."):
    stats = get_dashboard_stats(company_id)
    all_jobs = get_jobs(company_id, status=None)
    all_estimates = get_estimates(company_id)

# ── Client lookup map ─────────────────────────────────────────────────────────
try:
    all_clients_list = get_clients(company_id)
    client_map = {c["id"]: c for c in all_clients_list}
except Exception:
    client_map = {}

# ─────────────────────────────────────────────────────────────────────────────
# ROW 1 — Metric cards
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Overview")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        render_metric_card(
            "Total Clients",
            stats["total_clients"],
            icon="👥",
        ),
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        render_metric_card(
            "Active Jobs",
            stats["active_jobs"],
            icon="🔨",
        ),
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        render_metric_card(
            "Open Estimates",
            stats["open_estimates"],
            icon="📝",
        ),
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        render_metric_card(
            "Revenue This Month",
            format_currency(stats["revenue_this_month"]),
            icon="💰",
        ),
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 2 — Recent Jobs | Recent Estimates
# ─────────────────────────────────────────────────────────────────────────────
left_col, right_col = st.columns(2)

# ── Recent Jobs ───────────────────────────────────────────────────────────────
with left_col:
    st.markdown(
        '<div class="card"><div style="font-weight:700;font-size:1rem;color:#1F2937;margin-bottom:0.75rem;">🔨 Recent Jobs</div>',
        unsafe_allow_html=True,
    )

    recent_jobs = all_jobs[:5]
    if recent_jobs:
        # Table header
        st.markdown(
            """
            <table class="data-table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Client</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
            """,
            unsafe_allow_html=True,
        )
        for job in recent_jobs:
            client_id_j = job.get("client_id", "")
            client_name = client_map.get(client_id_j, {}).get("name", "—") if client_id_j else "—"
            badge = render_badge(job.get("status", "scheduled"))
            date_str = format_date(job.get("created_at", ""))
            title = job.get("title", "Untitled Job")
            st.markdown(
                f"<tr><td>{title}</td><td>{client_name}</td><td>{badge}</td><td>{date_str}</td></tr>",
                unsafe_allow_html=True,
            )
        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#9CA3AF;">No jobs yet</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)  # close card

    st.page_link("pages/3_Estimates.py", label="View All Jobs →")

# ── Recent Estimates ──────────────────────────────────────────────────────────
TRADE_ICONS = {
    "painting": "🎨",
    "electrical": "⚡",
    "landscaping": "🌿",
}

with right_col:
    st.markdown(
        '<div class="card"><div style="font-weight:700;font-size:1rem;color:#1F2937;margin-bottom:0.75rem;">📝 Recent Estimates</div>',
        unsafe_allow_html=True,
    )

    recent_estimates = all_estimates[:5]
    if recent_estimates:
        st.markdown(
            """
            <table class="data-table">
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Trade</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
            """,
            unsafe_allow_html=True,
        )
        for est in recent_estimates:
            client_id_e = est.get("client_id", "")
            client_name = client_map.get(client_id_e, {}).get("name", "—") if client_id_e else "—"
            trade = est.get("trade_type", "")
            trade_icon = TRADE_ICONS.get(trade, "🏠")
            trade_label = f"{trade_icon} {trade.title()}"
            total = format_currency(est.get("total", 0))
            badge = render_badge(est.get("status", "draft"))
            date_str = format_date(est.get("created_at", ""))
            st.markdown(
                f"<tr><td>{client_name}</td><td>{trade_label}</td><td>{total}</td><td>{badge}</td><td>{date_str}</td></tr>",
                unsafe_allow_html=True,
            )
        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#9CA3AF;">No estimates yet</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)  # close card

    st.page_link("pages/3_Estimates.py", label="View All Estimates →")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 3 — Quick Actions + Activity Feed
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Quick Actions")

qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("➕ New Estimate", use_container_width=True, key="dash_new_estimate"):
        st.switch_page("pages/3_Estimates.py")
with qa2:
    if st.button("👤 Add Client", use_container_width=True, key="dash_add_client"):
        st.switch_page("pages/2_Clients.py")
with qa3:
    if st.button("📅 Schedule Job", use_container_width=True, key="dash_schedule"):
        st.info("Navigate to the Scheduling page to add jobs to the calendar.")
with qa4:
    if st.button("🔄 Refresh", use_container_width=True, key="dash_refresh"):
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Activity Feed ─────────────────────────────────────────────────────────────
st.markdown("### Recent Activity")

activity = stats.get("recent_activity", [])

if activity:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for item in activity:
        item_type = item.get("type", "")
        icon = "🔨" if item_type == "job" else "📝"
        title = item.get("title", "")
        detail = item.get("detail", "")
        time_raw = item.get("time", "")
        time_str = format_date(time_raw) if time_raw else ""

        st.markdown(
            f"""
            <div style="display:flex;align-items:flex-start;padding:0.75rem 0;
                        border-bottom:1px solid #F3F4F6;">
              <div style="font-size:1.4rem;margin-right:0.75rem;min-width:2rem;">{icon}</div>
              <div style="flex:1;">
                <div style="font-weight:600;color:#1F2937;font-size:0.9rem;">{title}</div>
                <div style="color:#6B7280;font-size:0.82rem;">{detail}</div>
              </div>
              <div style="color:#9CA3AF;font-size:0.78rem;white-space:nowrap;">{time_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(
        """
        <div style="text-align:center;padding:3rem 1rem;color:#9CA3AF;
                    background:white;border-radius:12px;border:1px solid #F3F4F6;">
          <div style="font-size:3rem;">🚀</div>
          <div style="font-size:1.1rem;font-weight:700;color:#374151;margin-top:0.5rem;">
            No activity yet
          </div>
          <div style="font-size:0.9rem;margin-top:0.25rem;">
            Your activity will appear here as you use the platform.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Footer stats row ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
f1, f2, f3 = st.columns(3)
with f1:
    st.metric("Jobs This Month", stats.get("jobs_this_month", 0))
with f2:
    st.metric("Total Revenue (All Time)", format_currency(stats.get("total_revenue", 0)))
with f3:
    now = datetime.now()
    st.metric("Today's Date", now.strftime("%B %d, %Y"))
