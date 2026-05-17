import streamlit as st
import base64
import folium
from datetime import datetime, date
from streamlit_folium import folium_static

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
    get_jobs,
    get_job,
    create_job,
    update_job,
    get_jobs_by_client,
    get_clients,
    get_client,
    get_users_by_company,
    create_schedule_entry,
    get_schedule_by_job,
    update_schedule_entry,
    delete_schedule_entry,
    assign_crew,
    get_crew_for_schedule,
    get_crew_assignments_by_job,
    update_crew_assignment,
    create_media_record,
    get_job_media,
    create_notification,
    get_estimates,
    get_notifications,
)
from utils.gmail_integration import send_appointment_reminder

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Jobs | ServicePro OS",
    page_icon="🔨",
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

TRADE_ICONS = {"painting": "🎨", "electrical": "⚡", "landscaping": "🌿"}

STATUSES = {
    "scheduled": {"label": "Scheduled", "color": "#3B82F6", "icon": "📅"},
    "in_progress": {"label": "In Progress", "color": "#10B981", "icon": "🔨"},
    "on_hold": {"label": "On Hold", "color": "#F59E0B", "icon": "⏸"},
    "completed": {"label": "Completed", "color": "#6B7280", "icon": "✅"},
}

# ── Session state defaults ────────────────────────────────────────────────────
if "selected_job_id" not in st.session_state:
    st.session_state.selected_job_id = None
if "show_new_job_form" not in st.session_state:
    st.session_state.show_new_job_form = False
if "confirm_delete_job" not in st.session_state:
    st.session_state.confirm_delete_job = None


# ── Helper: build a single-marker folium map ──────────────────────────────────
def _single_job_map(lat, lng, title):
    m = folium.Map(location=[lat, lng], zoom_start=14)
    folium.Marker(
        [lat, lng],
        popup=title,
        tooltip=title,
        icon=folium.Icon(color="green", icon="wrench", prefix="fa"),
    ).add_to(m)
    return m


def _jobs_overview_map(jobs):
    """Build a folium map showing all jobs with lat/lng."""
    located = [j for j in jobs if j.get("lat") and j.get("lng")]
    if not located:
        return None
    center_lat = sum(j["lat"] for j in located) / len(located)
    center_lng = sum(j["lng"] for j in located) / len(located)
    m = folium.Map(location=[center_lat, center_lng], zoom_start=11)
    status_colors = {
        "scheduled": "blue",
        "in_progress": "green",
        "on_hold": "orange",
        "completed": "gray",
    }
    for j in located:
        color = status_colors.get(j.get("status", "scheduled"), "blue")
        folium.Marker(
            [j["lat"], j["lng"]],
            popup=f"{j.get('title','Job')}<br>{j.get('address','')}",
            tooltip=j.get("title", "Job"),
            icon=folium.Icon(color=color, icon="wrench", prefix="fa"),
        ).add_to(m)
    return m


def _get_google_maps_url(address):
    encoded = address.replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"


# ═══════════════════════════════════════════════════════════════════════════════
# JOB DETAIL VIEW
# ═══════════════════════════════════════════════════════════════════════════════
def render_job_detail(job_id):
    try:
        job = get_job(job_id)
    except Exception:
        job = None

    if not job:
        st.error("Job not found.")
        if st.button("← Back to Jobs"):
            st.session_state.selected_job_id = None
            st.rerun()
        return

    # ── Back button ──────────────────────────────────────────────────────────
    if st.button("← Back to Jobs", key="back_btn"):
        st.session_state.selected_job_id = None
        st.rerun()

    # ── Job header ───────────────────────────────────────────────────────────
    trade = job.get("trade_type", "")
    trade_icon = TRADE_ICONS.get(trade, "🏠")
    status = job.get("status", "scheduled")
    progress = job.get("progress", 0) or 0

    st.markdown(
        f"""
        <div style="background:white;border-radius:16px;padding:1.5rem 2rem;
                    border:1px solid #F3F4F6;box-shadow:0 2px 8px rgba(0,0,0,0.06);
                    margin-bottom:1rem;">
          <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
            <div style="font-size:2.5rem;">{trade_icon}</div>
            <div style="flex:1;">
              <h2 style="margin:0;color:#1F2937;font-size:1.6rem;font-weight:800;">
                {job.get('title','Untitled Job')}
              </h2>
              <div style="margin-top:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                {render_badge(status)}
                <span style="color:#6B7280;font-size:0.9rem;">Progress: {progress}%</span>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Action buttons row ───────────────────────────────────────────────────
    act1, act2, act3, act4 = st.columns(4)

    with act1:
        new_status = st.selectbox(
            "Update Status",
            list(STATUSES.keys()),
            index=list(STATUSES.keys()).index(status) if status in STATUSES else 0,
            format_func=lambda s: STATUSES[s]["label"],
            key=f"status_sel_{job_id}",
        )
        if st.button("Save Status", key=f"save_status_{job_id}"):
            try:
                update_job(job_id, {"status": new_status})
                create_notification(
                    user_id, "info",
                    f"Job status updated",
                    f"{job.get('title','')} → {STATUSES[new_status]['label']}",
                )
                st.success("Status updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update status: {e}")

    with act2:
        new_progress = st.slider(
            "Progress %", 0, 100, progress, key=f"prog_slider_{job_id}"
        )
        if st.button("Save Progress", key=f"save_prog_{job_id}"):
            try:
                update_job(job_id, {"progress": new_progress})
                st.success("Progress updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update progress: {e}")

    with act3:
        address_parts = " ".join(
            filter(None, [
                job.get("address", ""),
                job.get("city", ""),
                job.get("state", ""),
                job.get("zip", ""),
            ])
        )
        if address_parts:
            maps_url = _get_google_maps_url(address_parts)
            st.link_button("🗺 Get Directions", maps_url, use_container_width=True)
        else:
            st.info("No address set")

    with act4:
        if st.button("🤖 Generate Job Summary", key=f"ai_summary_{job_id}", use_container_width=True):
            try:
                from utils.claude_ai import generate_job_summary
                with st.spinner("Generating AI summary..."):
                    summary = generate_job_summary(job)
                st.session_state[f"ai_summary_text_{job_id}"] = summary
            except Exception as e:
                st.error(f"AI summary failed: {e}")

        if f"ai_summary_text_{job_id}" in st.session_state:
            with st.expander("AI Job Summary", expanded=True):
                st.markdown(st.session_state[f"ai_summary_text_{job_id}"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 5 Tabs ───────────────────────────────────────────────────────────────
    tab_overview, tab_crew, tab_media, tab_schedule, tab_notes = st.tabs(
        ["📋 Overview", "👷 Crew", "📸 Photos & Media", "📅 Schedule", "📝 Notes & Activity"]
    )

    # ─── TAB 1: Overview ────────────────────────────────────────────────────
    with tab_overview:
        client_data = {}
        if job.get("client_id"):
            try:
                client_data = get_client(job["client_id"]) or {}
            except Exception:
                client_data = {}

        col_info, col_map = st.columns([1, 1])

        with col_info:
            st.markdown("#### Job Information")
            info_rows = [
                ("Client", client_data.get("name", "—")),
                ("Trade", f"{trade_icon} {trade.title()}" if trade else "—"),
                ("Status", STATUSES.get(status, {}).get("label", status)),
                ("Progress", f"{progress}%"),
                ("Start Date", format_date(job.get("start_date"))),
                ("End Date", format_date(job.get("end_date"))),
                ("Address", address_parts or "—"),
            ]
            table_rows = "".join(
                f"<tr><td style='font-weight:600;color:#6B7280;padding:6px 12px 6px 0;white-space:nowrap;'>{k}</td>"
                f"<td style='padding:6px 0;color:#1F2937;'>{v}</td></tr>"
                for k, v in info_rows
            )
            st.markdown(
                f"<table style='width:100%;border-collapse:collapse;'>{table_rows}</table>",
                unsafe_allow_html=True,
            )

            if client_data.get("email"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Send Appointment Reminder")
                reminder_date = st.date_input(
                    "Appointment Date", value=date.today(), key=f"rem_date_{job_id}"
                )
                reminder_time = st.time_input(
                    "Appointment Time", key=f"rem_time_{job_id}"
                )
                if st.button("📧 Send Reminder to Client", key=f"send_rem_{job_id}"):
                    try:
                        result = send_appointment_reminder(
                            client_email=client_data["email"],
                            client_name=client_data.get("name", "Client"),
                            job_title=job.get("title", "Your Job"),
                            date=str(reminder_date),
                            time=str(reminder_time),
                            address=address_parts or "TBD",
                        )
                        if result:
                            st.success("Reminder sent successfully!")
                        else:
                            st.warning("Reminder could not be sent. Check Gmail settings.")
                    except Exception as e:
                        st.error(f"Error sending reminder: {e}")
            else:
                st.info("No client email configured. Add an email to the client to send reminders.")

        with col_map:
            st.markdown("#### Job Location")
            if job.get("lat") and job.get("lng"):
                try:
                    m = _single_job_map(job["lat"], job["lng"], job.get("title", "Job"))
                    folium_static(m, height=300)
                except Exception as e:
                    st.info(f"Map could not load: {e}")
            else:
                st.info("No location data. Geocode the address to see a map.")

        # Progress timeline
        st.markdown("#### Status Timeline")
        try:
            notifications = get_notifications(user_id)
            job_title = job.get("title", "")
            related = [
                n for n in notifications
                if job_title.lower() in (n.get("content", "") + n.get("title", "")).lower()
            ]
            if related:
                for n in related[:10]:
                    ts = format_date(n.get("created_at", ""))
                    st.markdown(
                        f"""
                        <div style="display:flex;gap:1rem;align-items:flex-start;
                                    padding:0.5rem 0;border-bottom:1px solid #F3F4F6;">
                          <div style="width:8px;height:8px;border-radius:50%;
                                      background:#10B981;margin-top:6px;flex-shrink:0;"></div>
                          <div>
                            <div style="font-weight:600;font-size:0.88rem;color:#1F2937;">
                              {n.get('title','')}
                            </div>
                            <div style="font-size:0.8rem;color:#6B7280;">{n.get('content','')} — {ts}</div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No status history recorded yet.")
        except Exception:
            st.info("Could not load activity timeline.")

    # ─── TAB 2: Crew ────────────────────────────────────────────────────────
    with tab_crew:
        st.markdown("#### Assigned Crew")
        try:
            assignments = get_crew_assignments_by_job(job_id)
        except Exception:
            assignments = []

        if assignments:
            for asgn in assignments:
                u = asgn.get("users") or {}
                asgn_status = asgn.get("status", "assigned")
                status_color = {"assigned": "#3B82F6", "checked_in": "#10B981", "checked_out": "#6B7280"}.get(asgn_status, "#6B7280")
                status_label = asgn_status.replace("_", " ").title()
                name = u.get("name", "Unknown")
                initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "?"

                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1:
                        st.markdown(
                            f"""
                            <div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;">
                              <div style="width:38px;height:38px;border-radius:50%;background:#10B981;
                                          color:white;display:flex;align-items:center;justify-content:center;
                                          font-weight:700;font-size:0.9rem;flex-shrink:0;">{initials}</div>
                              <div>
                                <div style="font-weight:600;color:#1F2937;">{name}</div>
                                <div style="font-size:0.8rem;color:#6B7280;">{u.get('role','')}</div>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f'<span style="background:{status_color}22;color:{status_color};'
                            f'padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600;">'
                            f'{status_label}</span>',
                            unsafe_allow_html=True,
                        )
                    with c3:
                        if asgn_status == "assigned":
                            if st.button("Clock In", key=f"ci_{asgn['id']}"):
                                try:
                                    update_crew_assignment(
                                        asgn["id"],
                                        {"status": "checked_in", "check_in_time": datetime.utcnow().isoformat()},
                                    )
                                    st.success(f"{name} clocked in!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        elif asgn_status == "checked_in":
                            if st.button("Clock Out", key=f"co_{asgn['id']}"):
                                try:
                                    update_crew_assignment(
                                        asgn["id"],
                                        {"status": "checked_out", "check_out_time": datetime.utcnow().isoformat()},
                                    )
                                    st.success(f"{name} clocked out!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        else:
                            st.markdown(
                                '<span style="color:#6B7280;font-size:0.82rem;">Completed</span>',
                                unsafe_allow_html=True,
                            )
                st.markdown("<hr style='margin:0.25rem 0;border-color:#F3F4F6;'>", unsafe_allow_html=True)
        else:
            st.info("No crew assigned to this job yet.")

        st.markdown("#### Assign Crew Member")
        try:
            all_users = get_users_by_company(company_id)
        except Exception:
            all_users = []

        if all_users:
            assigned_ids = {a.get("user_id") for a in assignments}
            available = [u for u in all_users if u["id"] not in assigned_ids]
            if available:
                sel_user = st.selectbox(
                    "Select crew member",
                    available,
                    format_func=lambda u: f"{u['name']} ({u['role']})",
                    key=f"assign_user_{job_id}",
                )
                assign_role = st.selectbox(
                    "Assignment role",
                    ["crew", "lead", "supervisor"],
                    key=f"assign_role_{job_id}",
                )
                if st.button("Assign to Job", key=f"do_assign_{job_id}"):
                    try:
                        assign_crew({
                            "job_id": job_id,
                            "user_id": sel_user["id"],
                            "role": assign_role,
                            "status": "assigned",
                        })
                        st.success(f"{sel_user['name']} assigned!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Assignment failed: {e}")
            else:
                st.info("All company users are already assigned to this job.")
        else:
            st.info("No users found in your company.")

    # ─── TAB 3: Photos & Media ───────────────────────────────────────────────
    with tab_media:
        st.markdown("#### Job Photos & Files")
        try:
            media_items = get_job_media(job_id)
        except Exception:
            media_items = []

        if media_items:
            cols_per_row = 3
            rows = [media_items[i:i+cols_per_row] for i in range(0, len(media_items), cols_per_row)]
            for row in rows:
                cols = st.columns(cols_per_row)
                for col, item in zip(cols, row):
                    with col:
                        uploader_name = (item.get("users") or {}).get("name", "Unknown")
                        media_type = item.get("media_type", "photo")
                        filename = item.get("filename", "file")
                        caption = item.get("caption", "")
                        uploaded_at = format_date(item.get("created_at", ""))
                        st.markdown(
                            f"""
                            <div style="background:#F9FAFB;border-radius:10px;padding:0.75rem;
                                        border:1px solid #E5E7EB;margin-bottom:0.5rem;">
                              <div style="font-size:2rem;text-align:center;margin-bottom:0.5rem;">
                                {'📸' if media_type == 'photo' else '📄'}
                              </div>
                              <div style="font-size:0.82rem;font-weight:600;color:#1F2937;
                                          word-break:break-all;">{filename}</div>
                              <div style="font-size:0.75rem;color:#6B7280;margin-top:4px;">
                                By: {uploader_name}<br>{uploaded_at}
                              </div>
                              {f'<div style="font-size:0.78rem;color:#374151;margin-top:4px;font-style:italic;">{caption}</div>' if caption else ''}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        else:
            st.markdown(
                '<div style="text-align:center;padding:2rem;color:#9CA3AF;">'
                '<div style="font-size:2.5rem;">📸</div>'
                '<div style="margin-top:0.5rem;">No photos or files yet.</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown("#### Upload New Files")
        uploaded_files = st.file_uploader(
            "Upload job photos or documents",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
            key=f"upload_{job_id}",
        )
        if uploaded_files:
            for uf in uploaded_files:
                caption_input = st.text_input(
                    f"Caption for {uf.name}",
                    key=f"caption_{job_id}_{uf.name}",
                )
            if st.button("Save Uploads", key=f"save_uploads_{job_id}"):
                saved_count = 0
                for uf in uploaded_files:
                    try:
                        file_bytes = uf.read()
                        b64_data = base64.b64encode(file_bytes).decode("utf-8")
                        caption_val = st.session_state.get(f"caption_{job_id}_{uf.name}", "")
                        media_type = "photo" if uf.type.startswith("image") else "document"
                        create_media_record({
                            "job_id": job_id,
                            "uploaded_by": user_id,
                            "filename": uf.name,
                            "storage_path": b64_data[:500],
                            "media_type": media_type,
                            "caption": caption_val,
                        })
                        saved_count += 1
                    except Exception as e:
                        st.error(f"Failed to save {uf.name}: {e}")
                if saved_count:
                    st.success(f"Saved {saved_count} file(s)!")
                    st.rerun()

    # ─── TAB 4: Schedule ────────────────────────────────────────────────────
    with tab_schedule:
        st.markdown("#### Scheduled Entries")
        try:
            schedule_entries = get_schedule_by_job(job_id)
        except Exception:
            schedule_entries = []

        if schedule_entries:
            for entry in schedule_entries:
                entry_date = format_date(entry.get("date", ""))
                start_t = entry.get("start_time", "")
                end_t = entry.get("end_time", "")
                time_range = f"{start_t} – {end_t}" if start_t and end_t else start_t or end_t or "All day"
                notes = entry.get("notes", "")

                # Crew for this schedule entry
                try:
                    sch_crew = get_crew_for_schedule(entry["id"])
                except Exception:
                    sch_crew = []

                crew_names = ", ".join(
                    (c.get("users") or {}).get("name", "?") for c in sch_crew
                ) or "No crew assigned"

                with st.expander(f"📅 {entry_date} — {time_range}", expanded=False):
                    st.markdown(
                        f"""
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.9rem;">
                          <div><span style="color:#6B7280;font-weight:600;">Date:</span> {entry_date}</div>
                          <div><span style="color:#6B7280;font-weight:600;">Time:</span> {time_range}</div>
                          <div><span style="color:#6B7280;font-weight:600;">Crew:</span> {crew_names}</div>
                          <div><span style="color:#6B7280;font-weight:600;">Notes:</span> {notes or '—'}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("Delete Entry", key=f"del_sch_{entry['id']}"):
                        try:
                            delete_schedule_entry(entry["id"])
                            st.success("Schedule entry deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No schedule entries yet for this job.")

        st.markdown("#### Add Schedule Entry")
        with st.form(key=f"add_schedule_{job_id}"):
            sch_date = st.date_input("Date", value=date.today(), key=f"sch_date_{job_id}")
            c1, c2 = st.columns(2)
            with c1:
                sch_start = st.time_input("Start Time", key=f"sch_start_{job_id}")
            with c2:
                sch_end = st.time_input("End Time", key=f"sch_end_{job_id}")
            try:
                all_users = get_users_by_company(company_id)
            except Exception:
                all_users = []
            sch_crew_sel = st.multiselect(
                "Assign Crew",
                all_users,
                format_func=lambda u: u["name"],
                key=f"sch_crew_{job_id}",
            )
            sch_notes = st.text_input("Notes", key=f"sch_notes_{job_id}")
            submitted = st.form_submit_button("Schedule")
            if submitted:
                try:
                    entry_data = {
                        "job_id": job_id,
                        "company_id": company_id,
                        "date": str(sch_date),
                        "start_time": str(sch_start),
                        "end_time": str(sch_end),
                        "notes": sch_notes,
                    }
                    new_entry = create_schedule_entry(entry_data)
                    if new_entry:
                        for crew_member in sch_crew_sel:
                            assign_crew({
                                "schedule_id": new_entry["id"],
                                "job_id": job_id,
                                "user_id": crew_member["id"],
                                "role": "crew",
                                "status": "assigned",
                            })
                        st.success("Schedule entry created!")
                        st.rerun()
                    else:
                        st.error("Failed to create schedule entry.")
                except Exception as e:
                    st.error(f"Error creating schedule: {e}")

    # ─── TAB 5: Notes & Activity ─────────────────────────────────────────────
    with tab_notes:
        st.markdown("#### Job Notes")
        current_notes = job.get("notes", "") or ""
        updated_notes = st.text_area(
            "Notes",
            value=current_notes,
            height=180,
            key=f"notes_area_{job_id}",
        )
        if st.button("Save Notes", key=f"save_notes_{job_id}"):
            try:
                update_job(job_id, {"notes": updated_notes})
                st.success("Notes saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving notes: {e}")

        st.markdown("---")
        st.markdown("#### AI Job Summary")
        if st.button("Generate AI Summary", key=f"ai_tab_sum_{job_id}"):
            try:
                from utils.claude_ai import generate_job_summary
                with st.spinner("Generating summary with AI..."):
                    summary_text = generate_job_summary(job)
                st.session_state[f"tab_ai_summary_{job_id}"] = summary_text
            except Exception as e:
                st.error(f"AI summary failed: {e}")

        if f"tab_ai_summary_{job_id}" in st.session_state:
            st.markdown(
                f"""
                <div style="background:#F0FDF4;border-left:4px solid #10B981;
                            border-radius:8px;padding:1rem 1.25rem;margin-top:0.75rem;">
                  <div style="font-weight:700;color:#065F46;margin-bottom:0.5rem;">AI Summary</div>
                  <div style="color:#1F2937;font-size:0.9rem;line-height:1.6;">
                    {st.session_state[f'tab_ai_summary_{job_id}']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("#### Activity Log")
        try:
            all_notifs = get_notifications(user_id)
            job_title = job.get("title", "")
            related_notifs = [
                n for n in all_notifs
                if job_title.lower() in (n.get("content", "") + n.get("title", "")).lower()
            ]
            if related_notifs:
                for n in related_notifs[:15]:
                    ts = format_date(n.get("created_at", ""))
                    ntype = n.get("type", "info")
                    type_color = {"info": "#3B82F6", "success": "#10B981", "warning": "#F59E0B", "error": "#EF4444"}.get(ntype, "#6B7280")
                    st.markdown(
                        f"""
                        <div style="display:flex;gap:0.75rem;align-items:flex-start;
                                    padding:0.6rem 0;border-bottom:1px solid #F3F4F6;">
                          <div style="width:8px;height:8px;border-radius:50%;
                                      background:{type_color};margin-top:5px;flex-shrink:0;"></div>
                          <div style="flex:1;">
                            <div style="font-weight:600;font-size:0.87rem;color:#1F2937;">
                              {n.get('title','')}
                            </div>
                            <div style="font-size:0.78rem;color:#6B7280;">{n.get('content','')} — {ts}</div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No activity recorded for this job.")
        except Exception:
            st.info("Could not load activity log.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">⚡ ServicePro OS</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="margin-bottom:0.5rem;">
          <div style="font-weight:700;font-size:1rem;color:#1F2937;">
            {company.get('name','My Company')}
          </div>
          <div style="font-size:0.85rem;color:#6B7280;">{user.get('name','')}</div>
          <div style="margin-top:4px;">{render_badge(role)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

# ── If a job is selected, show detail view ────────────────────────────────────
if st.session_state.selected_job_id:
    render_page_header("🔨 Job Detail", "Manage job details, crew, and schedule")
    render_job_detail(st.session_state.selected_job_id)
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header("🔨 Active Jobs", "Track and manage all your field jobs")

# ── Top bar: view toggle + new job button ─────────────────────────────────────
top_left, top_right = st.columns([3, 1])
with top_left:
    view_mode = st.radio(
        "View",
        ["🗂 Kanban", "📋 List", "🗺 Map"],
        horizontal=True,
        key="jobs_view_mode",
    )
with top_right:
    if st.button("➕ New Job", use_container_width=True, key="btn_new_job"):
        st.session_state.show_new_job_form = not st.session_state.show_new_job_form

# ── New Job Form ──────────────────────────────────────────────────────────────
if st.session_state.show_new_job_form:
    with st.expander("➕ Create New Job", expanded=True):
        with st.form("new_job_form"):
            st.markdown("#### New Job Details")
            job_title = st.text_input("Job Title *")

            c1, c2 = st.columns(2)
            with c1:
                try:
                    clients_list = get_clients(company_id)
                except Exception:
                    clients_list = []
                selected_client = st.selectbox(
                    "Client *",
                    clients_list,
                    format_func=lambda c: c["name"],
                    key="new_job_client",
                ) if clients_list else None

                trade_type = st.selectbox(
                    "Trade Type",
                    ["painting", "electrical", "landscaping"],
                    format_func=lambda t: t.title(),
                    key="new_job_trade",
                )
            with c2:
                try:
                    approved_estimates = get_estimates(company_id, status="approved")
                except Exception:
                    approved_estimates = []
                estimate_options = [None] + approved_estimates
                linked_estimate = st.selectbox(
                    "Linked Estimate (optional)",
                    estimate_options,
                    format_func=lambda e: "None" if e is None else f"{e.get('trade_type','').title()} — ${float(e.get('total',0) or 0):,.2f}",
                    key="new_job_estimate",
                )

                start_date = st.date_input("Start Date", key="new_job_start")

            st.markdown("#### Location")
            address = st.text_input("Street Address", key="new_job_addr")
            ci, cs, cz = st.columns(3)
            with ci:
                city = st.text_input("City", key="new_job_city")
            with cs:
                state = st.text_input("State", key="new_job_state")
            with cz:
                zip_code = st.text_input("ZIP", key="new_job_zip")

            end_date = st.date_input("End Date", key="new_job_end")
            description = st.text_area("Description", key="new_job_desc", height=100)
            initial_notes = st.text_area("Initial Notes", key="new_job_notes", height=80)

            submitted = st.form_submit_button("Create Job")
            if submitted:
                if not job_title:
                    st.error("Job Title is required.")
                elif not selected_client:
                    st.error("Please select a client.")
                else:
                    try:
                        lat, lng = None, None
                        if address and city and state:
                            try:
                                from utils.maps import geocode_address
                                full_addr = f"{address}, {city}, {state} {zip_code}"
                                coords = geocode_address(full_addr, company.get("google_maps_key", ""))
                                if coords:
                                    lat, lng = coords
                            except Exception:
                                pass

                        job_data = {
                            "company_id": company_id,
                            "client_id": selected_client["id"],
                            "estimate_id": linked_estimate["id"] if linked_estimate else None,
                            "title": job_title,
                            "trade_type": trade_type,
                            "address": address,
                            "city": city,
                            "state": state,
                            "zip": zip_code,
                            "lat": lat,
                            "lng": lng,
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                            "description": description,
                            "notes": initial_notes,
                            "status": "scheduled",
                            "progress": 0,
                        }
                        new_job = create_job(job_data)
                        if new_job:
                            create_notification(
                                user_id, "info",
                                "New job created",
                                f"{job_title} for {selected_client['name']}",
                            )
                            st.success(f"Job '{job_title}' created!")
                            st.session_state.show_new_job_form = False
                            st.rerun()
                        else:
                            st.error("Failed to create job. Please try again.")
                    except Exception as e:
                        st.error(f"Error creating job: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Load all jobs ─────────────────────────────────────────────────────────────
with st.spinner("Loading jobs..."):
    try:
        all_jobs = get_jobs(company_id)
    except Exception as e:
        st.error(f"Failed to load jobs: {e}")
        all_jobs = []

# ── Build client name lookup ──────────────────────────────────────────────────
try:
    all_clients = get_clients(company_id)
    client_map = {c["id"]: c for c in all_clients}
except Exception:
    client_map = {}

# ═══════════════════════════════════════════════════════════════════════════════
# KANBAN VIEW
# ═══════════════════════════════════════════════════════════════════════════════
if view_mode == "🗂 Kanban":
    if not all_jobs:
        st.markdown(
            '<div style="text-align:center;padding:3rem;color:#9CA3AF;">'
            '<div style="font-size:3rem;">🔨</div>'
            '<div style="font-size:1.1rem;font-weight:700;color:#374151;margin-top:0.5rem;">No jobs yet</div>'
            '<div style="font-size:0.9rem;">Click "New Job" to create your first job.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        grouped = {s: [] for s in STATUSES}
        for j in all_jobs:
            s = j.get("status", "scheduled")
            if s in grouped:
                grouped[s].append(j)
            else:
                grouped.setdefault(s, []).append(j)

        cols = st.columns(4)
        for col, (status_key, status_meta) in zip(cols, STATUSES.items()):
            with col:
                jobs_in_col = grouped.get(status_key, [])
                st.markdown(
                    f"""
                    <div style="background:#F9FAFB;border-radius:12px;padding:0.75rem;min-height:120px;">
                      <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
                        <div style="width:10px;height:10px;border-radius:50%;
                                    background:{status_meta['color']};"></div>
                        <span style="font-weight:700;font-size:0.82rem;color:#6B7280;
                                     text-transform:uppercase;letter-spacing:0.5px;">
                          {status_meta['icon']} {status_meta['label']}
                        </span>
                        <span style="background:#E5E7EB;color:#374151;border-radius:10px;
                                     padding:1px 7px;font-size:0.75rem;font-weight:700;margin-left:auto;">
                          {len(jobs_in_col)}
                        </span>
                      </div>
                    """,
                    unsafe_allow_html=True,
                )

                if not jobs_in_col:
                    st.markdown(
                        '<div style="text-align:center;padding:1.5rem;color:#9CA3AF;font-size:0.85rem;">No jobs</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    for j in jobs_in_col:
                        trade = j.get("trade_type", "")
                        trade_icon = TRADE_ICONS.get(trade, "🏠")
                        progress = j.get("progress", 0) or 0
                        client_info = client_map.get(j.get("client_id", ""), {})
                        client_name = client_info.get("name", "—")
                        start_d = format_date(j.get("start_date"))
                        end_d = format_date(j.get("end_date"))

                        st.markdown(
                            f"""
                            <div style="background:white;border-radius:8px;padding:0.75rem;
                                        margin-bottom:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.08);
                                        border-left:3px solid {status_meta['color']};">
                              <div style="font-weight:700;font-size:0.9rem;color:#1F2937;">
                                {trade_icon} {j.get('title','Untitled')}
                              </div>
                              <div style="font-size:0.8rem;color:#6B7280;margin-top:3px;">
                                {client_name}
                              </div>
                              <div style="font-size:0.75rem;color:#9CA3AF;margin-top:3px;">
                                {start_d} → {end_d}
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.progress(progress / 100)
                        if st.button(
                            "View Details",
                            key=f"kanban_view_{j['id']}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_job_id = j["id"]
                            st.rerun()
                        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LIST VIEW
# ═══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📋 List":
    # Filters
    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        search_query = st.text_input("🔍 Search jobs", placeholder="Job title or client name...", key="list_search")
    with fc2:
        status_filter = st.selectbox(
            "Status",
            ["All"] + [v["label"] for v in STATUSES.values()],
            key="list_status_filter",
        )
    with fc3:
        trade_filter = st.selectbox(
            "Trade",
            ["All", "Painting", "Electrical", "Landscaping"],
            key="list_trade_filter",
        )

    filtered_jobs = all_jobs
    if search_query:
        sq = search_query.lower()
        filtered_jobs = [
            j for j in filtered_jobs
            if sq in j.get("title", "").lower()
            or sq in client_map.get(j.get("client_id", ""), {}).get("name", "").lower()
        ]
    if status_filter != "All":
        status_key_map = {v["label"]: k for k, v in STATUSES.items()}
        sel_status = status_key_map.get(status_filter)
        if sel_status:
            filtered_jobs = [j for j in filtered_jobs if j.get("status") == sel_status]
    if trade_filter != "All":
        filtered_jobs = [j for j in filtered_jobs if j.get("trade_type", "").lower() == trade_filter.lower()]

    if not filtered_jobs:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#9CA3AF;">'
            '<div style="font-size:2rem;">🔍</div>'
            '<div style="font-weight:600;margin-top:0.5rem;">No jobs match your filters</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"**{len(filtered_jobs)} job(s) found**")
        st.markdown(
            """
            <table class="data-table" style="width:100%;">
              <thead><tr>
                <th>Title</th><th>Client</th><th>Trade</th><th>Status</th>
                <th>Progress</th><th>Start</th><th>End</th><th>Actions</th>
              </tr></thead><tbody>
            """,
            unsafe_allow_html=True,
        )
        for j in filtered_jobs:
            trade = j.get("trade_type", "")
            trade_icon = TRADE_ICONS.get(trade, "🏠")
            client_name = client_map.get(j.get("client_id", ""), {}).get("name", "—")
            status_badge = render_badge(j.get("status", "scheduled"))
            progress = j.get("progress", 0) or 0
            start_d = format_date(j.get("start_date"))
            end_d = format_date(j.get("end_date"))
            st.markdown(
                f"""
                <tr>
                  <td style="font-weight:600;">{j.get('title','—')}</td>
                  <td>{client_name}</td>
                  <td>{trade_icon} {trade.title() if trade else '—'}</td>
                  <td>{status_badge}</td>
                  <td>
                    <div style="background:#E5E7EB;border-radius:4px;height:6px;overflow:hidden;">
                      <div style="background:#10B981;height:100%;width:{progress}%;"></div>
                    </div>
                    <div style="font-size:0.75rem;color:#6B7280;">{progress}%</div>
                  </td>
                  <td style="font-size:0.85rem;">{start_d}</td>
                  <td style="font-size:0.85rem;">{end_d}</td>
                  <td></td>
                </tr>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</tbody></table>", unsafe_allow_html=True)

        # Action buttons outside the table
        st.markdown("<br>", unsafe_allow_html=True)
        for j in filtered_jobs:
            col_v, col_s, col_del = st.columns([2, 2, 1])
            with col_v:
                if st.button(f"View: {j.get('title','')[:30]}", key=f"list_view_{j['id']}"):
                    st.session_state.selected_job_id = j["id"]
                    st.rerun()
            with col_s:
                new_s = st.selectbox(
                    "Status",
                    list(STATUSES.keys()),
                    index=list(STATUSES.keys()).index(j.get("status", "scheduled"))
                    if j.get("status") in STATUSES else 0,
                    format_func=lambda s: STATUSES[s]["label"],
                    key=f"list_status_{j['id']}",
                    label_visibility="collapsed",
                )
                if st.button("Update", key=f"list_update_{j['id']}"):
                    try:
                        update_job(j["id"], {"status": new_s})
                        st.success("Updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col_del:
                if st.button("🗑", key=f"list_del_{j['id']}"):
                    st.session_state.confirm_delete_job = j["id"]
                if st.session_state.confirm_delete_job == j["id"]:
                    st.warning(f"Delete '{j.get('title')}'?")
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("Yes, Delete", key=f"confirm_del_{j['id']}"):
                            try:
                                update_job(j["id"], {"status": "cancelled"})
                                st.success("Job cancelled.")
                                st.session_state.confirm_delete_job = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    with c_no:
                        if st.button("Cancel", key=f"cancel_del_{j['id']}"):
                            st.session_state.confirm_delete_job = None
                            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# MAP VIEW
# ═══════════════════════════════════════════════════════════════════════════════
elif view_mode == "🗺 Map":
    st.markdown("#### All Jobs Map")
    jobs_with_location = [j for j in all_jobs if j.get("lat") and j.get("lng")]

    if not jobs_with_location:
        st.info(
            "No jobs have location data yet. When you create jobs with a valid address, "
            "they will appear on this map after geocoding."
        )
    else:
        try:
            m = _jobs_overview_map(all_jobs)
            if m:
                folium_static(m, height=500)
        except Exception as e:
            st.error(f"Map could not be rendered: {e}")

        # Map legend
        st.markdown(
            """
            <div style="display:flex;gap:1rem;flex-wrap:wrap;margin:0.5rem 0;">
              <div style="display:flex;align-items:center;gap:6px;font-size:0.85rem;">
                <div style="width:12px;height:12px;border-radius:50%;background:#3B82F6;"></div>Scheduled
              </div>
              <div style="display:flex;align-items:center;gap:6px;font-size:0.85rem;">
                <div style="width:12px;height:12px;border-radius:50%;background:#10B981;"></div>In Progress
              </div>
              <div style="display:flex;align-items:center;gap:6px;font-size:0.85rem;">
                <div style="width:12px;height:12px;border-radius:50%;background:#F59E0B;"></div>On Hold
              </div>
              <div style="display:flex;align-items:center;gap:6px;font-size:0.85rem;">
                <div style="width:12px;height:12px;border-radius:50%;background:#6B7280;"></div>Completed
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Job list below map
    st.markdown("#### Job Locations")
    for j in all_jobs:
        addr_parts = " ".join(filter(None, [j.get("address",""), j.get("city",""), j.get("state",""), j.get("zip","")]))
        client_name = client_map.get(j.get("client_id",""), {}).get("name", "—")
        trade = j.get("trade_type","")
        trade_icon = TRADE_ICONS.get(trade, "🏠")
        has_loc = bool(j.get("lat") and j.get("lng"))

        col_info, col_action = st.columns([3, 1])
        with col_info:
            st.markdown(
                f"""
                <div style="padding:0.5rem 0;border-bottom:1px solid #F3F4F6;">
                  <div style="font-weight:600;color:#1F2937;">{trade_icon} {j.get('title','—')}</div>
                  <div style="font-size:0.82rem;color:#6B7280;">{client_name} — {addr_parts or 'No address'}</div>
                  <div style="margin-top:3px;">{render_badge(j.get('status','scheduled'))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_action:
            if addr_parts:
                maps_url = _get_google_maps_url(addr_parts)
                st.link_button("Get Directions", maps_url, use_container_width=True)
            if st.button("Details", key=f"map_details_{j['id']}"):
                st.session_state.selected_job_id = j["id"]
                st.rerun()
