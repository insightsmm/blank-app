"""
WordPress SEO Agent Monitor
----------------------------
A Streamlit dashboard that connects to the Insight SEO Agent WordPress plugin
via its REST API endpoints:
  GET  /wp-json/insight-seo/v1/stats
  GET  /wp-json/insight-seo/v1/logs
  POST /wp-json/insight-seo/v1/run
"""

import streamlit as st
import requests
import json
from datetime import datetime

# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="WordPress SEO Agent Monitor",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; max-width: 1200px;}

    .stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.4rem;
        font-weight: 600;
        font-size: 14px;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
    .stButton > button:disabled { opacity: 0.5; cursor: not-allowed; }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .metric-number {
        font-size: 2.4rem;
        font-weight: 800;
        color: #1d2327;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 6px;
        font-weight: 500;
    }

    .score-green  { color: #10B981; font-weight: 700; }
    .score-orange { color: #F59E0B; font-weight: 700; }
    .score-red    { color: #EF4444; font-weight: 700; }

    .log-box {
        background: #1d2327;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 14px 16px;
        font-family: 'SFMono-Regular', Consolas, monospace;
        font-size: 12px;
        line-height: 1.6;
        height: 380px;
        overflow-y: auto;
        color: #a8b5c0;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .status-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-published  { background:#d1fae5; color:#065f46; }
    .badge-processing { background:#dbeafe; color:#1e40af; }
    .badge-failed     { background:#fee2e2; color:#991b1b; }
    .badge-skipped    { background:#f3f4f6; color:#6b7280; }
    .badge-active     { background:#d1fae5; color:#065f46; }
    .badge-inactive   { background:#fee2e2; color:#991b1b; }

    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1d2327;
        margin: 1rem 0 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
defaults = {
    "connected": False,
    "last_stats": None,
    "last_logs": None,
    "last_refresh": None,
    "run_result": None,
    "connection_error": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# Sidebar — credentials
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## WordPress Connection")
    wp_url = st.text_input(
        "WP Site URL",
        placeholder="https://insightsm.com",
        help="Your WordPress site URL (no trailing slash).",
    )
    wp_user = st.text_input(
        "WP Username",
        help="WordPress admin username.",
    )
    wp_pass = st.text_input(
        "Application Password",
        type="password",
        help="Generate at WP Admin > Users > Profile > Application Passwords.",
    )

    connect_btn = st.button("Connect", use_container_width=True)

    if st.session_state.connected:
        st.success("Connected")
    elif st.session_state.connection_error:
        st.error(st.session_state.connection_error)

    st.markdown("---")
    st.markdown("### Quick Links")
    if wp_url:
        base = wp_url.rstrip("/")
        st.markdown(
            f"[WP Admin]({base}/wp-admin/) | "
            f"[SEO Agent]({base}/wp-admin/admin.php?page=insight-chatgpt-agents-app) | "
            f"[Drafts]({base}/wp-admin/edit.php?post_status=draft&post_type=post)"
        )
    else:
        st.caption("Enter the site URL to see quick links.")

    st.markdown("---")
    st.caption("Insight SEO Agent Monitor v2.0")

# ─────────────────────────────────────────────
# REST API helpers
# ─────────────────────────────────────────────

def api_get(endpoint: str) -> dict:
    """Perform authenticated GET to the plugin REST API."""
    url = wp_url.rstrip("/") + "/wp-json/insight-seo/v1/" + endpoint.lstrip("/")
    resp = requests.get(url, auth=(wp_user, wp_pass), timeout=20)
    resp.raise_for_status()
    return resp.json()


def api_post(endpoint: str, data: dict = None) -> dict:
    """Perform authenticated POST to the plugin REST API."""
    url = wp_url.rstrip("/") + "/wp-json/insight-seo/v1/" + endpoint.lstrip("/")
    resp = requests.post(url, auth=(wp_user, wp_pass), json=data or {}, timeout=120)
    resp.raise_for_status()
    return resp.json()


def wp_get(endpoint: str, params: dict = None) -> list | dict:
    """Perform authenticated GET to the WP REST API v2."""
    url = wp_url.rstrip("/") + "/wp-json/wp/v2/" + endpoint.lstrip("/")
    resp = requests.get(url, auth=(wp_user, wp_pass), params=params or {}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_all_data():
    """Fetch stats, logs, and drafts from the WP site."""
    stats = api_get("stats")
    logs  = api_get("logs")
    return stats, logs


def test_connection(url: str, user: str, password: str) -> tuple[bool, str]:
    """Test connectivity to the WP site and the plugin REST API."""
    if not url or not user or not password:
        return False, "Fill in all fields."
    try:
        resp = requests.get(
            url.rstrip("/") + "/wp-json/insight-seo/v1/stats",
            auth=(user, password),
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, f"Connected! Agent active: {data.get('agent_active', 'unknown')}"
        if resp.status_code == 401:
            return False, "Authentication failed — check username and application password."
        if resp.status_code == 403:
            return False, "Permission denied — user must have manage_options capability."
        if resp.status_code == 404:
            return False, "Plugin REST API not found. Is the Insight SEO Agent plugin activated?"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect — check URL and network."
    except requests.exceptions.Timeout:
        return False, "Request timed out."
    except Exception as exc:
        return False, str(exc)


# ─────────────────────────────────────────────
# Handle connect button
# ─────────────────────────────────────────────
if connect_btn:
    with st.spinner("Connecting..."):
        ok, msg = test_connection(wp_url, wp_user, wp_pass)
        st.session_state.connected = ok
        st.session_state.connection_error = None if ok else msg
        if ok:
            try:
                stats, logs = fetch_all_data()
                st.session_state.last_stats = stats
                st.session_state.last_logs  = logs
                st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
            except Exception as exc:
                st.session_state.connection_error = f"Connected but failed to load data: {exc}"
        st.rerun()

# ─────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────

st.markdown("# WordPress SEO Agent Monitor")

if not st.session_state.connected:
    st.info("Enter your WordPress credentials in the sidebar and click **Connect** to get started.")

    st.markdown("---")
    st.markdown("## About This Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **This dashboard monitors the Insight SEO Agent WordPress plugin.**

        The plugin automatically:
        - Detects new draft posts and pages
        - Optimises SEO using Claude AI
        - Adds relevant images from Pexels
        - Publishes when SEO score reaches 85+

        **Requirements:**
        - Insight SEO Agent plugin installed & activated
        - WordPress Application Password (WP 5.6+)
        - Claude API key configured in the plugin
        """)
    with col2:
        st.markdown("""
        **REST API Endpoints used:**
        - `GET /wp-json/insight-seo/v1/stats` — Agent stats
        - `GET /wp-json/insight-seo/v1/logs` — Processing logs
        - `POST /wp-json/insight-seo/v1/run` — Trigger agent cycle

        **To generate an Application Password:**
        1. Log in to WP Admin
        2. Go to Users → Your Profile
        3. Scroll to "Application Passwords"
        4. Enter a name and click "Add New"
        5. Copy the generated password (shown once)
        """)
    st.stop()

# ─────────────────────────────────────────────
# Connected — show dashboard
# ─────────────────────────────────────────────

stats = st.session_state.last_stats or {}
logs  = st.session_state.last_logs  or {}

# Top action bar
header_col1, header_col2, header_col3, header_col4 = st.columns([2, 2, 2, 1])

with header_col1:
    agent_active = stats.get("agent_active", False)
    badge_cls    = "badge-active" if agent_active else "badge-inactive"
    badge_text   = "Agent Active" if agent_active else "Agent Inactive"
    st.markdown(
        f'<span class="status-badge {badge_cls}">{badge_text}</span>',
        unsafe_allow_html=True,
    )
    if stats.get("next_cron"):
        st.caption(f"Next cron: {stats['next_cron']}")

with header_col2:
    trigger_btn = st.button("Trigger Agent Cycle", use_container_width=True)

with header_col3:
    refresh_btn = st.button("Refresh Data", use_container_width=True)

with header_col4:
    if st.session_state.last_refresh:
        st.caption(f"Updated: {st.session_state.last_refresh}")

# ─── Trigger agent cycle ───
if trigger_btn:
    with st.spinner("Running agent cycle on the WordPress site... (this may take 30-90s)"):
        try:
            result = api_post("run")
            st.session_state.run_result = result
            # Refresh data after run
            stats, logs = fetch_all_data()
            st.session_state.last_stats   = stats
            st.session_state.last_logs    = logs
            st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
        except requests.exceptions.HTTPError as exc:
            st.error(f"API error: {exc}")
        except Exception as exc:
            st.error(f"Error triggering cycle: {exc}")
    st.rerun()

# Show run result if available
if st.session_state.run_result:
    r = st.session_state.run_result
    processed  = r.get("processed", 0)
    published  = r.get("published", 0)
    failed     = r.get("failed", 0)
    skipped    = r.get("skipped", 0)
    st.success(
        f"Cycle complete — Processed: **{processed}**, Published: **{published}**, "
        f"Failed: **{failed}**, Skipped: **{skipped}**"
    )
    if st.button("Dismiss", key="dismiss_run"):
        st.session_state.run_result = None
        st.rerun()

# ─── Refresh data ───
if refresh_btn:
    with st.spinner("Refreshing..."):
        try:
            stats, logs = fetch_all_data()
            st.session_state.last_stats   = stats
            st.session_state.last_logs    = logs
            st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
        except Exception as exc:
            st.error(f"Refresh failed: {exc}")
    st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────
# Stat cards
# ─────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)

draft_count     = stats.get("draft_count", "–")
published_today = stats.get("published_today", "–")
avg_score       = stats.get("avg_score", 0)
total_processed = stats.get("total_processed", "–")

score_color = "#10B981" if avg_score >= 85 else ("#F59E0B" if avg_score >= 70 else "#EF4444")

with s1:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-number">{draft_count}</div>'
        f'<div class="metric-label">Draft Posts</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with s2:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-number" style="color:#10B981">{published_today}</div>'
        f'<div class="metric-label">Published Today</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with s3:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-number" style="color:{score_color}">{avg_score}</div>'
        f'<div class="metric-label">Avg SEO Score</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with s4:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-number">{total_processed}</div>'
        f'<div class="metric-label">Total Processed</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────
# Two-column layout: DB logs + Activity log
# ─────────────────────────────────────────────
left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown('<div class="section-header">Recent Processing Log</div>', unsafe_allow_html=True)

    db_logs = logs.get("db_logs", [])

    if not db_logs:
        st.info("No posts have been processed yet.")
    else:
        # Build display table
        rows = []
        for entry in db_logs[:20]:
            score_after = entry.get("seo_score_after", 0)
            if isinstance(score_after, str):
                try:
                    score_after = int(score_after)
                except ValueError:
                    score_after = 0

            score_cls = "score-green" if score_after >= 85 else ("score-orange" if score_after >= 70 else "score-red")
            status    = entry.get("status", "unknown")
            badge_cls = f"badge-{status}" if status in ("published", "processing", "failed", "skipped") else "badge-processing"

            rows.append({
                "Title":   (entry.get("post_title") or "(untitled)")[:50],
                "Type":    entry.get("post_type", "post"),
                "Before":  entry.get("seo_score_before", 0),
                "After":   score_after,
                "Status":  status.capitalize(),
                "Iters":   entry.get("iterations", 0),
                "Date":    (entry.get("processed_at") or "")[:16],
            })

        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

with right_col:
    st.markdown('<div class="section-header">Activity Log</div>', unsafe_allow_html=True)

    activity_lines = logs.get("activity_log", [])
    if activity_lines:
        log_text = "\n".join(str(line) for line in activity_lines[-100:])
    else:
        log_text = "(No activity logged yet.)"

    st.markdown(
        f'<div class="log-box">{log_text}</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────
# Current drafts (live from WP REST API)
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Current Draft Posts</div>', unsafe_allow_html=True)

try:
    draft_posts = wp_get("posts", {"status": "draft", "per_page": 20})
    draft_pages = wp_get("pages", {"status": "draft", "per_page": 10})

    all_drafts = []
    for p in (draft_posts if isinstance(draft_posts, list) else []):
        all_drafts.append({
            "ID":      p.get("id"),
            "Type":    "Post",
            "Title":   (p.get("title", {}).get("rendered") or "")[:60],
            "Slug":    p.get("slug", ""),
            "Created": (p.get("date") or "")[:10],
        })
    for p in (draft_pages if isinstance(draft_pages, list) else []):
        all_drafts.append({
            "ID":      p.get("id"),
            "Type":    "Page",
            "Title":   (p.get("title", {}).get("rendered") or "")[:60],
            "Slug":    p.get("slug", ""),
            "Created": (p.get("date") or "")[:10],
        })

    if all_drafts:
        import pandas as pd
        df_drafts = pd.DataFrame(all_drafts)
        st.dataframe(df_drafts, use_container_width=True, hide_index=True)
    else:
        st.success("No draft posts found — all caught up!")

except requests.exceptions.HTTPError as exc:
    if exc.response.status_code == 401:
        st.warning("Cannot load drafts: authentication failed.")
    else:
        st.warning(f"Could not load drafts: HTTP {exc.response.status_code}")
except Exception as exc:
    st.warning(f"Could not load current drafts: {exc}")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Insight SEO Agent Monitor — powered by Claude AI & Pexels. "
    f"Plugin REST API: `{wp_url.rstrip('/') if wp_url else '[site URL]'}/wp-json/insight-seo/v1/`"
)
