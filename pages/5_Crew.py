import streamlit as st
import secrets
import string
from datetime import datetime, date

from utils.auth import check_authentication, is_role
from utils.styles import (
    inject_css,
    render_badge,
    render_page_header,
    format_currency,
    format_date,
    COLORS,
)
from utils.db import (
    get_users_by_company,
    get_user,
    create_user,
    update_user,
    get_schedule,
    get_crew_assignments_by_job,
    get_crew_for_schedule,
    get_jobs,
    create_notification,
)
from utils.gmail_integration import send_email

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crew | ServicePro OS",
    page_icon="👷",
    layout="wide",
)

# ── Auth guard ────────────────────────────────────────────────────────────────
if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()

# ── Convenience vars ──────────────────────────────────────────────────────────
user = st.session_state.user
company = st.session_state.company
role = st.session_state.role
company_id = company["id"]
user_id = user["id"]

# ── Session defaults ──────────────────────────────────────────────────────────
if "show_add_crew_form" not in st.session_state:
    st.session_state.show_add_crew_form = False
if "edit_crew_member_id" not in st.session_state:
    st.session_state.edit_crew_member_id = None
if "crew_schedule_offset" not in st.session_state:
    st.session_state.crew_schedule_offset = 0


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _initials(name):
    parts = (name or "?").split()
    return "".join(p[0].upper() for p in parts[:2])


def _status_dot_color(member_status):
    return {
        "clocked_in": "#10B981",
        "on_job": "#3B82F6",
        "off_duty": "#9CA3AF",
    }.get(member_status, "#9CA3AF")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">⚡ ServicePro OS</div>', unsafe_allow_html=True)
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
    st.markdown("---")

# ── Auth check for sensitive actions ─────────────────────────────────────────
can_manage = is_role("owner", "admin")

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header("👷 Crew Management", "Manage your field team")

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading crew data..."):
    try:
        crew_members = get_users_by_company(company_id)
    except Exception as e:
        st.error(f"Failed to load crew: {e}")
        crew_members = []

    today_str = str(date.today())
    try:
        todays_schedule = get_schedule(company_id, date_from=today_str, date_to=today_str)
    except Exception:
        todays_schedule = []

    # Build crew assignments for today to determine status
    today_crew_ids_active = set()
    for entry in todays_schedule:
        try:
            sch_crew = get_crew_for_schedule(entry["id"])
            for ca in sch_crew:
                if ca.get("status") == "checked_in":
                    today_crew_ids_active.add(ca.get("user_id"))
        except Exception:
            pass

    try:
        all_jobs = get_jobs(company_id)
    except Exception:
        all_jobs = []

    # Build job lookup
    job_map = {j["id"]: j for j in all_jobs}

# ═══════════════════════════════════════════════════════════════════════════════
# TOP STATS ROW
# ═══════════════════════════════════════════════════════════════════════════════
stat_cols = st.columns(4)

total_crew = len(crew_members)
clocked_in_count = len(today_crew_ids_active)
jobs_today = len(todays_schedule)

# Active assignments — sum all non-completed assignments today
active_assignments = 0
for entry in todays_schedule:
    try:
        sch_crew = get_crew_for_schedule(entry["id"])
        active_assignments += sum(1 for ca in sch_crew if ca.get("status") == "assigned")
    except Exception:
        pass

with stat_cols[0]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div style="font-size:1.5rem;">👷</div>
          <div class="metric-number">{total_crew}</div>
          <div class="metric-label">Total Crew Members</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat_cols[1]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div style="font-size:1.5rem;">🟢</div>
          <div class="metric-number">{clocked_in_count}</div>
          <div class="metric-label">Clocked In Today</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat_cols[2]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div style="font-size:1.5rem;">🔨</div>
          <div class="metric-number">{active_assignments}</div>
          <div class="metric-label">Active Assignments</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat_cols[3]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div style="font-size:1.5rem;">📅</div>
          <div class="metric-number">{jobs_today}</div>
          <div class="metric-label">Scheduled Today</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TWO-COLUMN LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1, 1], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
# LEFT — Crew Member List
# ─────────────────────────────────────────────────────────────────────────────
with left_col:
    header_c1, header_c2 = st.columns([2, 1])
    with header_c1:
        st.markdown("### Crew Members")
    with header_c2:
        if can_manage:
            if st.button("➕ Add Member", use_container_width=True, key="btn_add_crew"):
                st.session_state.show_add_crew_form = not st.session_state.show_add_crew_form

    # ── Add Crew Member Form ──────────────────────────────────────────────────
    if st.session_state.show_add_crew_form and can_manage:
        with st.expander("➕ Add New Crew Member", expanded=True):
            with st.form("add_crew_form"):
                st.markdown("#### New Team Member")
                new_name = st.text_input("Full Name *", key="new_crew_name")
                new_email = st.text_input("Email *", key="new_crew_email")
                new_phone = st.text_input("Phone", key="new_crew_phone")
                new_role = st.selectbox(
                    "Role",
                    ["owner", "admin", "estimator", "crew_lead", "field_tech", "client"],
                    format_func=lambda r: r.replace("_", " ").title(),
                    key="new_crew_role",
                )
                use_auto_pw = st.checkbox("Auto-generate password", value=True, key="auto_pw")
                manual_pw = ""
                if not use_auto_pw:
                    manual_pw = st.text_input("Password", type="password", key="new_crew_pw")
                send_welcome = st.checkbox("Send welcome email with credentials", value=True, key="send_welcome_email")

                submitted = st.form_submit_button("Add Member")
                if submitted:
                    if not new_name or not new_email:
                        st.error("Name and email are required.")
                    else:
                        pw = _generate_password() if use_auto_pw else manual_pw
                        if not pw:
                            st.error("Password is required.")
                        else:
                            try:
                                new_member = create_user({
                                    "company_id": company_id,
                                    "name": new_name,
                                    "email": new_email,
                                    "phone": new_phone,
                                    "role": new_role,
                                    "password": pw,
                                    "is_active": True,
                                })
                                if new_member:
                                    create_notification(
                                        user_id, "info",
                                        "New crew member added",
                                        f"{new_name} joined as {new_role.replace('_',' ').title()}",
                                    )
                                    if send_welcome:
                                        try:
                                            send_email(
                                                to_email=new_email,
                                                subject=f"Welcome to {company.get('name','ServicePro OS')}",
                                                body_html=f"""
                                                <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
                                                  <h2 style="color:#10B981;">Welcome, {new_name}!</h2>
                                                  <p>You've been added to <strong>{company.get('name','')}</strong> on ServicePro OS.</p>
                                                  <div style="background:#F0FDF4;border-radius:8px;padding:1rem;margin:1rem 0;">
                                                    <strong>Your login credentials:</strong><br>
                                                    Email: {new_email}<br>
                                                    Password: {pw}
                                                  </div>
                                                  <p>Please log in and change your password.</p>
                                                </div>
                                                """,
                                            )
                                        except Exception:
                                            pass
                                    st.success(f"{new_name} added successfully!")
                                    st.session_state.show_add_crew_form = False
                                    st.rerun()
                                else:
                                    st.error("Failed to create crew member.")
                            except Exception as e:
                                st.error(f"Error: {e}")

    # ── Crew Member Cards ─────────────────────────────────────────────────────
    if not crew_members:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#9CA3AF;">'
            '<div style="font-size:2.5rem;">👷</div>'
            '<div style="font-weight:600;margin-top:0.5rem;">No crew members yet</div>'
            '<div style="font-size:0.85rem;">Add your first team member above.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for member in crew_members:
            member_id = member["id"]
            name = member.get("name", "Unknown")
            m_role = member.get("role", "crew")
            m_email = member.get("email", "")
            m_phone = member.get("phone", "")
            initials = _initials(name)
            is_clocked_in = member_id in today_crew_ids_active
            dot_color = "#10B981" if is_clocked_in else "#9CA3AF"
            status_label = "🟢 Clocked In" if is_clocked_in else "⚪ Off Duty"
            is_editing = st.session_state.edit_crew_member_id == member_id

            st.markdown(
                f"""
                <div style="background:white;border-radius:12px;padding:1rem;
                            border:1px solid #F3F4F6;margin-bottom:0.75rem;
                            box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                  <div style="display:flex;align-items:center;gap:0.75rem;">
                    <div style="width:44px;height:44px;border-radius:50%;
                                background:linear-gradient(135deg,#10B981,#3B82F6);
                                color:white;display:flex;align-items:center;
                                justify-content:center;font-weight:700;font-size:1rem;
                                flex-shrink:0;">{initials}</div>
                    <div style="flex:1;min-width:0;">
                      <div style="font-weight:700;color:#1F2937;font-size:0.95rem;">{name}</div>
                      <div style="font-size:0.8rem;color:#6B7280;">{m_role.replace('_',' ').title()}</div>
                      <div style="display:flex;gap:0.75rem;margin-top:4px;flex-wrap:wrap;">
                        {f'<span style="font-size:0.78rem;color:#6B7280;">📞 {m_phone}</span>' if m_phone else ''}
                        {f'<span style="font-size:0.78rem;color:#6B7280;">✉ {m_email}</span>' if m_email else ''}
                      </div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                      <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#374151;">
                        <div style="width:8px;height:8px;border-radius:50%;background:{dot_color};"></div>
                        {status_label}
                      </div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_c1, btn_c2, btn_c3 = st.columns(3)
            with btn_c1:
                if st.button("📅 Schedule", key=f"view_sch_{member_id}", use_container_width=True):
                    st.session_state[f"show_member_schedule_{member_id}"] = not st.session_state.get(
                        f"show_member_schedule_{member_id}", False
                    )
            with btn_c2:
                if st.button("✉ Message", key=f"msg_{member_id}", use_container_width=True):
                    if m_email:
                        try:
                            send_email(
                                to_email=m_email,
                                subject=f"Message from {user.get('name','')} at {company.get('name','')}",
                                body_html=f"""
                                <div style="font-family:Arial,sans-serif;">
                                  <p>Hi {name},</p>
                                  <p>This is a message from {user.get('name','')} at {company.get('name','')}.</p>
                                  <p>Please check the ServicePro OS portal for any updates.</p>
                                </div>
                                """,
                            )
                            st.success(f"Message sent to {name}!")
                        except Exception as e:
                            st.error(f"Failed to send message: {e}")
                    else:
                        st.warning("No email address for this crew member.")
            with btn_c3:
                if can_manage:
                    if st.button("✏ Edit", key=f"edit_{member_id}", use_container_width=True):
                        if st.session_state.edit_crew_member_id == member_id:
                            st.session_state.edit_crew_member_id = None
                        else:
                            st.session_state.edit_crew_member_id = member_id
                        st.rerun()

            # ── Edit form ────────────────────────────────────────────────────
            if is_editing and can_manage:
                with st.expander(f"Edit {name}", expanded=True):
                    with st.form(f"edit_crew_{member_id}"):
                        edit_name = st.text_input("Name", value=name, key=f"ename_{member_id}")
                        edit_phone = st.text_input("Phone", value=m_phone, key=f"ephone_{member_id}")
                        edit_role = st.selectbox(
                            "Role",
                            ["owner", "admin", "estimator", "crew_lead", "field_tech", "client"],
                            index=["owner", "admin", "estimator", "crew_lead", "field_tech", "client"].index(m_role)
                            if m_role in ["owner", "admin", "estimator", "crew_lead", "field_tech", "client"] else 0,
                            format_func=lambda r: r.replace("_", " ").title(),
                            key=f"erole_{member_id}",
                        )
                        edit_active = st.checkbox(
                            "Active",
                            value=member.get("is_active", True),
                            key=f"eactive_{member_id}",
                        )
                        save_edit = st.form_submit_button("Save Changes")
                        if save_edit:
                            try:
                                update_user(member_id, {
                                    "name": edit_name,
                                    "phone": edit_phone,
                                    "role": edit_role,
                                    "is_active": edit_active,
                                })
                                st.success("Changes saved!")
                                st.session_state.edit_crew_member_id = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

            # ── Member schedule ───────────────────────────────────────────────
            if st.session_state.get(f"show_member_schedule_{member_id}", False):
                st.markdown(
                    f"<div style='background:#F9FAFB;border-radius:8px;padding:0.75rem;margin-bottom:0.75rem;'>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{name}'s schedule today:**")
                member_entries = []
                for entry in todays_schedule:
                    try:
                        sch_crew = get_crew_for_schedule(entry["id"])
                        for ca in sch_crew:
                            if ca.get("user_id") == member_id:
                                member_entries.append(entry)
                                break
                    except Exception:
                        pass
                if member_entries:
                    for e in member_entries:
                        job_info = e.get("jobs") or {}
                        job_title = job_info.get("title", "Unknown Job")
                        start_t = e.get("start_time", "")
                        end_t = e.get("end_time", "")
                        st.markdown(
                            f"- **{start_t} – {end_t}**: {job_title}",
                        )
                else:
                    st.markdown("_No assignments today._")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RIGHT — Today's Schedule
# ─────────────────────────────────────────────────────────────────────────────
with right_col:
    sch_hdr1, sch_hdr2, sch_hdr3 = st.columns([2, 1, 1])
    with sch_hdr1:
        offset = st.session_state.crew_schedule_offset
        if offset == 0:
            st.markdown("### Today's Schedule")
        elif offset == 1:
            st.markdown("### Tomorrow's Schedule")
        else:
            from datetime import timedelta
            target_date = date.today() + timedelta(days=offset)
            st.markdown(f"### Schedule — {target_date.strftime('%b %d')}")
    with sch_hdr2:
        if st.button("← Prev", key="sch_prev"):
            st.session_state.crew_schedule_offset = max(0, st.session_state.crew_schedule_offset - 1)
            st.rerun()
    with sch_hdr3:
        if st.button("Next →", key="sch_next"):
            st.session_state.crew_schedule_offset += 1
            st.rerun()

    from datetime import timedelta
    target_date = date.today() + timedelta(days=st.session_state.crew_schedule_offset)
    target_str = str(target_date)

    try:
        target_schedule = get_schedule(company_id, date_from=target_str, date_to=target_str)
    except Exception:
        target_schedule = []

    if not target_schedule:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#9CA3AF;">'
            '<div style="font-size:2.5rem;">📅</div>'
            '<div style="font-weight:600;margin-top:0.5rem;">No schedule entries</div>'
            '<div style="font-size:0.85rem;">No jobs are scheduled for this day.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        # Build time-slot timeline as styled cards
        time_slots = {}
        for entry in target_schedule:
            key = entry.get("start_time", "00:00") or "00:00"
            time_slots.setdefault(key, []).append(entry)

        for time_key in sorted(time_slots.keys()):
            entries = time_slots[time_key]
            for entry in entries:
                job_info = entry.get("jobs") or {}
                job_title = job_info.get("title", "Unknown Job")
                job_status = job_info.get("status", "scheduled")
                job_trade = job_info.get("trade_type", "")
                trade_icon = {"painting": "🎨", "electrical": "⚡", "landscaping": "🌿"}.get(job_trade, "🏠")
                start_t = entry.get("start_time", "") or ""
                end_t = entry.get("end_time", "") or ""
                time_range = f"{start_t} – {end_t}" if end_t else start_t

                try:
                    sch_crew = get_crew_for_schedule(entry["id"])
                except Exception:
                    sch_crew = []

                crew_names = []
                for ca in sch_crew:
                    u = ca.get("users") or {}
                    crew_names.append(u.get("name", "?"))
                crew_display = ", ".join(crew_names) if crew_names else "No crew"

                status_colors_map = {
                    "scheduled": "#3B82F6",
                    "in_progress": "#10B981",
                    "on_hold": "#F59E0B",
                    "completed": "#6B7280",
                }
                border_color = status_colors_map.get(job_status, "#E5E7EB")

                st.markdown(
                    f"""
                    <div style="background:white;border-radius:10px;padding:0.875rem;
                                margin-bottom:0.75rem;box-shadow:0 1px 4px rgba(0,0,0,0.07);
                                border-left:4px solid {border_color};">
                      <div style="display:flex;align-items:flex-start;gap:0.75rem;">
                        <div style="min-width:70px;text-align:center;">
                          <div style="font-size:0.82rem;font-weight:700;color:{border_color};">
                            {start_t[:5] if start_t else '—'}
                          </div>
                          <div style="font-size:0.72rem;color:#9CA3AF;">
                            {end_t[:5] if end_t else ''}
                          </div>
                        </div>
                        <div style="flex:1;min-width:0;">
                          <div style="font-weight:700;color:#1F2937;font-size:0.9rem;">
                            {trade_icon} {job_title}
                          </div>
                          <div style="font-size:0.8rem;color:#6B7280;margin-top:3px;">
                            👷 {crew_display}
                          </div>
                          {f'<div style="font-size:0.78rem;color:#9CA3AF;margin-top:2px;">{entry.get("notes","")}</div>' if entry.get("notes") else ""}
                        </div>
                        <div>{render_badge(job_status)}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ═══════════════════════════════════════════════════════════════════════════════
# CREW PERFORMANCE TABLE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Crew Performance This Month")

from datetime import timedelta
month_start = date.today().replace(day=1)
month_end = date.today()
month_start_str = str(month_start)
month_end_str = str(month_end)

try:
    month_schedule = get_schedule(company_id, date_from=month_start_str, date_to=month_end_str)
except Exception:
    month_schedule = []

# Aggregate per crew member
perf_data = {}
for member in crew_members:
    perf_data[member["id"]] = {
        "name": member.get("name", "?"),
        "role": member.get("role", "crew"),
        "jobs_completed": 0,
        "checkins": 0,
        "hours_worked": 0.0,
    }

for entry in month_schedule:
    try:
        sch_crew = get_crew_for_schedule(entry["id"])
        for ca in sch_crew:
            uid = ca.get("user_id")
            if uid and uid in perf_data:
                if ca.get("status") in ("checked_in", "checked_out"):
                    perf_data[uid]["checkins"] += 1
                if ca.get("status") == "checked_out":
                    perf_data[uid]["jobs_completed"] += 1
                    # Estimate hours from schedule entry
                    start_t = entry.get("start_time")
                    end_t = entry.get("end_time")
                    if start_t and end_t:
                        try:
                            from datetime import datetime as dt
                            fmt = "%H:%M:%S"
                            start_dt = dt.strptime(start_t, fmt)
                            end_dt = dt.strptime(end_t, fmt)
                            hrs = (end_dt - start_dt).seconds / 3600
                            perf_data[uid]["hours_worked"] += hrs
                        except Exception:
                            pass
    except Exception:
        pass

if perf_data:
    st.markdown(
        """
        <table class="data-table" style="width:100%;">
          <thead><tr>
            <th>Crew Member</th><th>Role</th>
            <th>Jobs Completed This Month</th><th>Hours Worked</th><th>Check-ins</th>
          </tr></thead><tbody>
        """,
        unsafe_allow_html=True,
    )
    for uid, data in perf_data.items():
        name = data["name"]
        initials = _initials(name)
        m_role = data["role"].replace("_", " ").title()
        jobs_done = data["jobs_completed"]
        hours = round(data["hours_worked"], 1)
        checkins = data["checkins"]

        st.markdown(
            f"""
            <tr>
              <td>
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="width:30px;height:30px;border-radius:50%;background:#10B981;
                              color:white;display:flex;align-items:center;justify-content:center;
                              font-weight:700;font-size:0.78rem;flex-shrink:0;">{initials}</div>
                  <span style="font-weight:600;">{name}</span>
                </div>
              </td>
              <td><span style="font-size:0.85rem;color:#6B7280;">{m_role}</span></td>
              <td style="text-align:center;">
                <span style="font-weight:700;color:#10B981;">{jobs_done}</span>
              </td>
              <td style="text-align:center;">
                <span style="font-weight:700;color:#3B82F6;">{hours}h</span>
              </td>
              <td style="text-align:center;">
                <span style="font-weight:700;color:#6B7280;">{checkins}</span>
              </td>
            </tr>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</tbody></table>", unsafe_allow_html=True)
else:
    st.info("No crew performance data available for this month.")
