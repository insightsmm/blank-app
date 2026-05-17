import streamlit as st
from datetime import datetime

COLORS = {
    "primary": "#10B981",
    "secondary": "#3B82F6",
    "danger": "#EF4444",
    "warning": "#F59E0B",
}

_CSS = """
<style>
/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Page container */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: white; border: none; border-radius: 10px;
    padding: 0.5rem 1.5rem; font-weight: 600; font-size: 0.9rem;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(16,185,129,0.3);
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(16,185,129,0.4); }
.stButton > button[kind="secondary"] {
    background: white; color: #374151; border: 1px solid #E5E7EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.stButton > button[kind="secondary"]:hover { background: #F9FAFB; }

/* Metric cards */
.metric-card {
    background: white; border-radius: 16px; padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border: 1px solid #F3F4F6;
    transition: box-shadow 0.2s;
}
.metric-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.metric-number { font-size: 2rem; font-weight: 800; color: #1F2937; line-height: 1.1; }
.metric-label { font-size: 0.85rem; color: #6B7280; margin-top: 4px; font-weight: 500; }
.metric-delta { font-size: 0.8rem; margin-top: 8px; font-weight: 600; }
.metric-delta.positive { color: #10B981; }
.metric-delta.negative { color: #EF4444; }

/* Status badges */
.badge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 600; letter-spacing: 0.3px;
}
.badge-scheduled { background: #DBEAFE; color: #1E40AF; }
.badge-in_progress { background: #D1FAE5; color: #065F46; }
.badge-on_hold { background: #FEF3C7; color: #92400E; }
.badge-completed { background: #D1FAE5; color: #065F46; }
.badge-cancelled { background: #FEE2E2; color: #991B1B; }
.badge-draft { background: #F3F4F6; color: #6B7280; }
.badge-sent { background: #DBEAFE; color: #1E40AF; }
.badge-approved { background: #D1FAE5; color: #065F46; }
.badge-pending { background: #FEF3C7; color: #92400E; }
.badge-paid { background: #D1FAE5; color: #065F46; }
.badge-failed { background: #FEE2E2; color: #991B1B; }

/* Page header */
.page-header {
    background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
    color: white; padding: 1.5rem 2rem; border-radius: 16px;
    margin-bottom: 1.5rem;
}
.page-header h1 { font-size: 1.8rem; font-weight: 800; margin: 0; color: white; }
.page-header p { margin: 4px 0 0 0; opacity: 0.9; font-size: 0.95rem; }

/* Cards */
.card {
    background: white; border-radius: 12px; padding: 1.25rem;
    border: 1px solid #F3F4F6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}

/* Chat messages */
.chat-message-user {
    background: #10B981; color: white;
    padding: 0.75rem 1rem; border-radius: 16px 16px 4px 16px;
    margin: 0.5rem 0; max-width: 75%; margin-left: auto;
    font-size: 0.9rem;
}
.chat-message-other {
    background: #F3F4F6; color: #1F2937;
    padding: 0.75rem 1rem; border-radius: 16px 16px 16px 4px;
    margin: 0.5rem 0; max-width: 75%;
    font-size: 0.9rem;
}
.chat-timestamp { font-size: 0.7rem; color: #9CA3AF; margin-top: 2px; }

/* Sidebar branding */
.sidebar-brand {
    font-size: 1.3rem; font-weight: 800; color: #10B981;
    padding: 1rem 0; border-bottom: 2px solid #E5E7EB; margin-bottom: 1rem;
}

/* Tables */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: #F9FAFB; font-weight: 600; font-size: 0.8rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 12px; border-bottom: 1px solid #E5E7EB; }
.data-table td { padding: 12px; border-bottom: 1px solid #F3F4F6; font-size: 0.9rem; }
.data-table tr:hover td { background: #F9FAFB; }

/* Form styling */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    border-radius: 8px !important;
    border-color: #E5E7EB !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #10B981 !important;
    box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important;
}

/* Kanban columns */
.kanban-col {
    background: #F9FAFB; border-radius: 12px; padding: 1rem;
    min-height: 200px;
}
.kanban-header {
    font-weight: 700; font-size: 0.85rem; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.75rem;
}
.kanban-card {
    background: white; border-radius: 8px; padding: 0.875rem;
    margin-bottom: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-left: 3px solid #10B981; cursor: pointer;
}
.kanban-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>
"""


def inject_css() -> None:
    """Inject the ServicePro OS global CSS into the Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value,
    delta: str = None,
    delta_positive: bool = True,
    icon: str = "📊",
) -> str:
    """Return an HTML metric card string."""
    delta_html = ""
    if delta is not None:
        delta_cls = "positive" if delta_positive else "negative"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div class="metric-delta {delta_cls}">{arrow} {delta}</div>'

    return (
        f'<div class="metric-card">'
        f'<div style="font-size:1.5rem">{icon}</div>'
        f'<div class="metric-number">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f"{delta_html}"
        f"</div>"
    )


def render_badge(status: str) -> str:
    """Return an HTML badge span for the given status string."""
    safe_status = str(status).lower().replace(" ", "_")
    label = str(status).replace("_", " ").title()
    return f'<span class="badge badge-{safe_status}">{label}</span>'


def render_page_header(title: str, subtitle: str = "") -> None:
    """Render the green-gradient page header."""
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1>{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


def render_card(content_html: str) -> None:
    """Wrap and render content HTML inside a card div."""
    st.markdown(
        f'<div class="card">{content_html}</div>',
        unsafe_allow_html=True,
    )


def format_currency(amount) -> str:
    """Format a numeric amount as a USD currency string."""
    try:
        return f"${float(amount or 0):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def format_date(dt) -> str:
    """Format a date or datetime object / ISO string as 'May 16, 2026'."""
    if dt is None:
        return ""
    try:
        if isinstance(dt, str):
            # Handle ISO format with or without time component
            dt = dt[:10]
            dt = datetime.strptime(dt, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except Exception:
        return str(dt)


def render_empty_state(
    icon: str,
    title: str,
    message: str,
    button_label: str = None,
) -> str:
    """Return an HTML empty state block."""
    button_html = (
        f'<div style="margin-top:1rem;">'
        f'<span style="background:#10B981;color:white;padding:0.5rem 1.5rem;'
        f'border-radius:10px;font-weight:600;cursor:pointer;">{button_label}</span>'
        f"</div>"
        if button_label
        else ""
    )
    return (
        f'<div style="text-align:center;padding:3rem 1rem;color:#6B7280;">'
        f'<div style="font-size:3rem;">{icon}</div>'
        f'<div style="font-size:1.2rem;font-weight:700;color:#374151;margin-top:0.5rem;">{title}</div>'
        f'<div style="font-size:0.9rem;margin-top:0.25rem;">{message}</div>'
        f"{button_html}"
        f"</div>"
    )
