import streamlit as st
import folium
from datetime import datetime, date, timedelta
from streamlit_folium import st_folium

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
    update_job,
    get_clients,
    get_client,
    get_users_by_company,
    create_schedule_entry,
    get_schedule,
    get_schedule_by_job,
    update_schedule_entry,
    delete_schedule_entry,
    assign_crew,
    get_crew_for_schedule,
    create_notification,
    get_crew_assignments_by_job,
)
from utils.gmail_integration import send_appointment_reminder

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Scheduling | ServicePro OS",
    page_icon="📅",
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

# ── Session defaults ──────────────────────────────────────────────────────────
if "schedule_week_offset" not in st.session_state:
    st.session_state.schedule_week_offset = 0

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

# ── Page header ───────────────────────────────────────────────────────────────
render_page_header("📅 Scheduling & Dispatch", "Plan your crew's week efficiently")

# ── Load base data ────────────────────────────────────────────────────────────
with st.spinner("Loading schedule data..."):
    try:
        all_jobs = get_jobs(company_id)
    except Exception as e:
        st.error(f"Failed to load jobs: {e}")
        all_jobs = []

    try:
        all_clients = get_clients(company_id)
        client_map = {c["id"]: c for c in all_clients}
    except Exception:
        client_map = {}

    try:
        all_users = get_users_by_company(company_id)
    except Exception:
        all_users = []

# Job maps
job_map = {j["id"]: j for j in all_jobs}
active_jobs = [j for j in all_jobs if j.get("status") in ("scheduled", "in_progress")]

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_calendar, tab_map, tab_conflicts = st.tabs(
    ["📅 Calendar View", "🗺 Map & Route Planning", "⚠ Conflict Detection"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CALENDAR VIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab_calendar:

    # ── Week navigation ───────────────────────────────────────────────────────
    today = date.today()
    # Find Monday of current week + offset
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday) + timedelta(weeks=st.session_state.schedule_week_offset)
    week_end = week_start + timedelta(days=6)

    nav_c1, nav_c2, nav_c3 = st.columns([1, 3, 1])
    with nav_c1:
        if st.button("← Previous Week", key="prev_week"):
            st.session_state.schedule_week_offset -= 1
            st.rerun()
    with nav_c2:
        st.markdown(
            f"""
            <div style="text-align:center;padding:0.5rem;">
              <div style="font-weight:700;font-size:1.1rem;color:#1F2937;">
                {week_start.strftime('%B %d')} — {week_end.strftime('%B %d, %Y')}
              </div>
              <div style="font-size:0.82rem;color:#6B7280;">
                Week {week_start.strftime('%W')} of {week_start.year}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_c3:
        if st.button("Next Week →", key="next_week"):
            st.session_state.schedule_week_offset += 1
            st.rerun()

    # ── Load week's schedule ──────────────────────────────────────────────────
    try:
        week_schedule = get_schedule(
            company_id,
            date_from=str(week_start),
            date_to=str(week_end),
        )
    except Exception as e:
        st.error(f"Failed to load schedule: {e}")
        week_schedule = []

    # Group entries by date
    schedule_by_day = {}
    for entry in week_schedule:
        d = entry.get("date", "")
        schedule_by_day.setdefault(d, []).append(entry)

    # ── 7-column week grid ────────────────────────────────────────────────────
    day_cols = st.columns(7)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for i, (col, day_name) in enumerate(zip(day_cols, day_names)):
        col_date = week_start + timedelta(days=i)
        col_date_str = str(col_date)
        is_today = col_date == today
        day_entries = schedule_by_day.get(col_date_str, [])

        with col:
            # Column header
            header_bg = "#10B981" if is_today else "#F9FAFB"
            header_color = "white" if is_today else "#6B7280"
            date_color = "white" if is_today else "#1F2937"

            st.markdown(
                f"""
                <div style="background:{header_bg};border-radius:8px 8px 0 0;
                            padding:0.5rem 0.25rem;text-align:center;margin-bottom:2px;">
                  <div style="font-weight:700;font-size:0.78rem;color:{header_color};
                               text-transform:uppercase;letter-spacing:0.5px;">{day_name}</div>
                  <div style="font-weight:800;font-size:1.1rem;color:{date_color};">
                    {col_date.day}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Day container
            st.markdown(
                '<div style="background:#F9FAFB;border-radius:0 0 8px 8px;'
                'padding:0.25rem;min-height:120px;">',
                unsafe_allow_html=True,
            )

            if not day_entries:
                st.markdown(
                    '<div style="text-align:center;padding:1rem 0.25rem;'
                    'color:#D1D5DB;font-size:0.75rem;">Empty</div>',
                    unsafe_allow_html=True,
                )
            else:
                for entry in day_entries:
                    job_info = entry.get("jobs") or {}
                    job_title = job_info.get("title", "Job")
                    job_status = job_info.get("status", "scheduled")
                    client_id = job_info.get("client_id", "")
                    client_info = client_map.get(client_id, {})
                    client_name = client_info.get("name", "")
                    start_t = (entry.get("start_time") or "")[:5]
                    end_t = (entry.get("end_time") or "")[:5]

                    try:
                        sch_crew = get_crew_for_schedule(entry["id"])
                    except Exception:
                        sch_crew = []

                    crew_initials = " ".join(
                        "".join(p[0].upper() for p in ((c.get("users") or {}).get("name", "?")).split()[:2])
                        for c in sch_crew[:3]
                    )

                    status_color = {
                        "scheduled": "#3B82F6",
                        "in_progress": "#10B981",
                        "on_hold": "#F59E0B",
                        "completed": "#6B7280",
                    }.get(job_status, "#E5E7EB")

                    st.markdown(
                        f"""
                        <div style="background:white;border-radius:6px;padding:0.4rem 0.5rem;
                                    margin-bottom:4px;border-left:3px solid {status_color};
                                    box-shadow:0 1px 2px rgba(0,0,0,0.06);">
                          <div style="font-size:0.72rem;color:{status_color};font-weight:700;">
                            {start_t}–{end_t}
                          </div>
                          <div style="font-size:0.78rem;font-weight:700;color:#1F2937;
                                      line-height:1.2;margin-top:2px;">
                            {job_title[:20]}{'…' if len(job_title)>20 else ''}
                          </div>
                          {f'<div style="font-size:0.7rem;color:#6B7280;">{client_name[:18]}</div>' if client_name else ''}
                          {f'<div style="font-size:0.68rem;color:#9CA3AF;margin-top:2px;">{crew_initials}</div>' if crew_initials else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    with st.expander(f"View: {job_title[:15]}", expanded=False):
                        st.markdown(
                            f"""
                            **Job:** {job_title}
                            **Client:** {client_name or '—'}
                            **Time:** {start_t} – {end_t}
                            **Status:** {job_status.replace('_',' ').title()}
                            **Crew:** {', '.join((c.get('users') or {}).get('name','?') for c in sch_crew) or 'None'}
                            **Notes:** {entry.get('notes','—')}
                            """
                        )
                        if st.button("Delete Entry", key=f"cal_del_{entry['id']}"):
                            try:
                                delete_schedule_entry(entry["id"])
                                st.success("Deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick Schedule Form ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Quick Schedule")

    with st.form("quick_schedule_form"):
        qs_c1, qs_c2 = st.columns(2)
        with qs_c1:
            sel_job = st.selectbox(
                "Select Job *",
                active_jobs,
                format_func=lambda j: f"{j.get('title','—')} ({j.get('status','').replace('_',' ').title()})",
                key="qs_job",
            ) if active_jobs else None

            qs_date = st.date_input("Date *", value=today, key="qs_date")
            qs_start = st.time_input("Start Time", key="qs_start")

        with qs_c2:
            qs_end = st.time_input("End Time", key="qs_end")
            qs_crew = st.multiselect(
                "Assign Crew",
                all_users,
                format_func=lambda u: f"{u['name']} ({u.get('role','').replace('_',' ').title()})",
                key="qs_crew",
            )
            qs_notes = st.text_input("Notes (optional)", key="qs_notes")

        send_reminder_check = st.checkbox("Send appointment reminder to client", key="qs_send_reminder")

        qs_submitted = st.form_submit_button("Schedule Job", use_container_width=True)
        if qs_submitted:
            if not sel_job:
                st.error("Please select a job.")
            else:
                try:
                    entry_data = {
                        "job_id": sel_job["id"],
                        "company_id": company_id,
                        "date": str(qs_date),
                        "start_time": str(qs_start),
                        "end_time": str(qs_end),
                        "notes": qs_notes,
                    }
                    new_entry = create_schedule_entry(entry_data)
                    if new_entry:
                        for crew_member in qs_crew:
                            assign_crew({
                                "schedule_id": new_entry["id"],
                                "job_id": sel_job["id"],
                                "user_id": crew_member["id"],
                                "role": "crew",
                                "status": "assigned",
                            })
                        create_notification(
                            user_id, "info",
                            "Job scheduled",
                            f"{sel_job['title']} on {qs_date}",
                        )
                        if send_reminder_check:
                            client_info = client_map.get(sel_job.get("client_id", ""), {})
                            if client_info.get("email"):
                                try:
                                    send_appointment_reminder(
                                        client_email=client_info["email"],
                                        client_name=client_info.get("name", "Client"),
                                        job_title=sel_job.get("title", "Your Job"),
                                        date=str(qs_date),
                                        time=str(qs_start),
                                        address=" ".join(filter(None, [
                                            sel_job.get("address",""),
                                            sel_job.get("city",""),
                                            sel_job.get("state",""),
                                        ])),
                                    )
                                    st.info("Reminder sent to client.")
                                except Exception:
                                    st.warning("Could not send reminder email.")
                        st.success(f"'{sel_job['title']}' scheduled for {qs_date}!")
                        st.rerun()
                    else:
                        st.error("Failed to create schedule entry.")
                except Exception as e:
                    st.error(f"Error scheduling job: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MAP & ROUTE PLANNING
# ═══════════════════════════════════════════════════════════════════════════════
with tab_map:
    st.markdown("### All Active Jobs Map")

    located_jobs = [j for j in active_jobs if j.get("lat") and j.get("lng")]

    if not located_jobs:
        st.info(
            "No active jobs have location data. Create jobs with a valid address "
            "and enable geocoding to see them on the map."
        )
    else:
        # Build folium map
        center_lat = sum(j["lat"] for j in located_jobs) / len(located_jobs)
        center_lng = sum(j["lng"] for j in located_jobs) / len(located_jobs)
        jobs_folium_map = folium.Map(location=[center_lat, center_lng], zoom_start=11)

        status_colors = {
            "scheduled": "blue",
            "in_progress": "green",
            "on_hold": "orange",
            "completed": "gray",
        }

        for j in located_jobs:
            color = status_colors.get(j.get("status", "scheduled"), "blue")
            trade = j.get("trade_type", "")
            trade_icon = TRADE_ICONS.get(trade, "🏠")
            client_name = client_map.get(j.get("client_id",""), {}).get("name","")
            addr = " ".join(filter(None, [j.get("address",""), j.get("city",""), j.get("state","")]))
            popup_html = f"""
            <div style='font-family:Arial,sans-serif;min-width:150px;'>
              <div style='font-weight:700;font-size:14px;'>{trade_icon} {j.get('title','Job')}</div>
              <div style='color:#6B7280;font-size:12px;'>{client_name}</div>
              <div style='color:#6B7280;font-size:12px;'>{addr}</div>
              <div style='margin-top:4px;'><span style='background:#E5E7EB;padding:2px 8px;
                border-radius:10px;font-size:11px;font-weight:600;'>
                {j.get('status','').replace('_',' ').title()}</span></div>
            </div>
            """
            folium.Marker(
                [j["lat"], j["lng"]],
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=j.get("title", "Job"),
                icon=folium.Icon(color=color, icon="wrench", prefix="fa"),
            ).add_to(jobs_folium_map)

        st_folium(jobs_folium_map, use_container_width=True, height=500)

        # Map legend
        st.markdown(
            """
            <div style="display:flex;gap:1rem;flex-wrap:wrap;margin:0.25rem 0 1rem;">
              <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;">
                <div style="width:10px;height:10px;border-radius:50%;background:#3B82F6;"></div>Scheduled
              </div>
              <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;">
                <div style="width:10px;height:10px;border-radius:50%;background:#10B981;"></div>In Progress
              </div>
              <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;">
                <div style="width:10px;height:10px;border-radius:50%;background:#F59E0B;"></div>On Hold
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Route Planner ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Route Planner")
    st.markdown("Plan an efficient route for your crew across multiple job sites.")

    rp_c1, rp_c2 = st.columns([1, 2])
    with rp_c1:
        company_address = company.get("address", "")
        start_location = st.text_input(
            "Starting Location",
            value=company_address,
            placeholder="e.g. 123 Main St, City, State",
            key="route_start",
        )

        today_str = str(date.today())
        try:
            today_schedule = get_schedule(company_id, date_from=today_str, date_to=today_str)
        except Exception:
            today_schedule = []

        # Get unique jobs in today's schedule
        today_job_ids = list({e.get("job_id") for e in today_schedule if e.get("job_id")})
        today_jobs_data = [job_map[jid] for jid in today_job_ids if jid in job_map]

        route_jobs = st.multiselect(
            "Select Jobs to Visit",
            today_jobs_data if today_jobs_data else active_jobs,
            format_func=lambda j: f"{j.get('title','—')} — {j.get('address','')} {j.get('city','')}",
            key="route_jobs",
        )

    with rp_c2:
        if route_jobs and st.button("🗺 Plan Route", key="plan_route_btn"):
            stops = []
            if start_location:
                stops.append(start_location.replace(" ", "+"))

            for rj in route_jobs:
                addr = " ".join(filter(None, [
                    rj.get("address", ""),
                    rj.get("city", ""),
                    rj.get("state", ""),
                    rj.get("zip", ""),
                ]))
                if addr:
                    stops.append(addr.replace(" ", "+"))

            if len(stops) >= 2:
                origin = stops[0]
                destination = stops[-1]
                waypoints = "|".join(stops[1:-1]) if len(stops) > 2 else ""
                maps_url = (
                    f"https://www.google.com/maps/dir/{origin}"
                    + (f"/{waypoints}" if waypoints else "")
                    + f"/{destination}"
                )

                st.link_button("🗺 Open Route in Google Maps", maps_url, use_container_width=True)

                # Estimated time
                num_stops = len(route_jobs)
                estimated_mins = 15 + (num_stops * 20)
                estimated_hrs = estimated_mins // 60
                estimated_remaining = estimated_mins % 60

                st.markdown(
                    f"""
                    <div style="background:#F0FDF4;border-left:4px solid #10B981;
                                border-radius:8px;padding:0.75rem 1rem;margin-top:0.75rem;">
                      <div style="font-weight:700;color:#065F46;font-size:0.9rem;">
                        Route Estimate
                      </div>
                      <div style="font-size:0.85rem;color:#374151;margin-top:4px;">
                        {num_stops} stop(s) — approx. {estimated_hrs}h {estimated_remaining}m total drive time
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Route map with lines
                if any(j.get("lat") and j.get("lng") for j in route_jobs):
                    located_route = [j for j in route_jobs if j.get("lat") and j.get("lng")]
                    if located_route:
                        route_map = folium.Map(
                            location=[located_route[0]["lat"], located_route[0]["lng"]],
                            zoom_start=11,
                        )
                        coords = [[j["lat"], j["lng"]] for j in located_route]
                        for idx, (j, coord) in enumerate(zip(located_route, coords)):
                            folium.Marker(
                                coord,
                                tooltip=f"Stop {idx+1}: {j.get('title','Job')}",
                                popup=f"Stop {idx+1}: {j.get('title','')}",
                                icon=folium.Icon(
                                    color="red" if idx == 0 else "blue",
                                    icon="flag" if idx == len(located_route)-1 else "wrench",
                                    prefix="fa",
                                ),
                            ).add_to(route_map)
                        if len(coords) > 1:
                            folium.PolyLine(coords, color="#3B82F6", weight=3, opacity=0.8).add_to(route_map)
                        st_folium(route_map, use_container_width=True, height=350)

                # Job order list
                st.markdown("#### Job Visit Order")
                for idx, rj in enumerate(route_jobs):
                    addr = " ".join(filter(None, [rj.get("address",""), rj.get("city",""), rj.get("state","")]))
                    client_name = client_map.get(rj.get("client_id",""), {}).get("name","")
                    trade = rj.get("trade_type","")
                    trade_icon = TRADE_ICONS.get(trade, "🏠")
                    st.markdown(
                        f"""
                        <div style="display:flex;align-items:center;gap:0.75rem;
                                    padding:0.6rem 0;border-bottom:1px solid #F3F4F6;">
                          <div style="width:26px;height:26px;border-radius:50%;background:#3B82F6;
                                      color:white;display:flex;align-items:center;justify-content:center;
                                      font-weight:700;font-size:0.82rem;flex-shrink:0;">{idx+1}</div>
                          <div style="flex:1;">
                            <div style="font-weight:600;color:#1F2937;font-size:0.9rem;">
                              {trade_icon} {rj.get('title','—')}
                            </div>
                            <div style="font-size:0.8rem;color:#6B7280;">{client_name} — {addr or 'No address'}</div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.warning("Need at least a starting location and one job to plan a route.")
        elif not route_jobs:
            st.info("Select jobs above to plan a route.")

    # ── Today's Dispatch ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Today's Dispatch")

    today_str = str(date.today())
    try:
        dispatch_schedule = get_schedule(company_id, date_from=today_str, date_to=today_str)
    except Exception:
        dispatch_schedule = []

    if not dispatch_schedule:
        st.info("No jobs scheduled for today. Use the Quick Schedule form in the Calendar tab to add some.")
    else:
        for entry in dispatch_schedule:
            job_info = entry.get("jobs") or {}
            job_id = entry.get("job_id", "")
            job_title = job_info.get("title", "Unknown Job")
            job_status = job_info.get("status", "scheduled")
            job_addr = " ".join(filter(None, [
                job_info.get("address", ""),
                job_info.get("city", ""),
            ]))
            start_t = (entry.get("start_time") or "")[:5]
            end_t = (entry.get("end_time") or "")[:5]
            time_range = f"{start_t} – {end_t}" if end_t else start_t or "All day"

            try:
                sch_crew = get_crew_for_schedule(entry["id"])
            except Exception:
                sch_crew = []
            crew_names = ", ".join((c.get("users") or {}).get("name", "?") for c in sch_crew) or "Unassigned"

            disp_c1, disp_c2, disp_c3 = st.columns([3, 2, 3])
            with disp_c1:
                trade = job_info.get("trade_type", "")
                trade_icon = TRADE_ICONS.get(trade, "🏠")
                st.markdown(
                    f"""
                    <div style="padding:0.5rem 0;">
                      <div style="font-weight:700;color:#1F2937;font-size:0.9rem;">
                        {trade_icon} {job_title}
                      </div>
                      <div style="font-size:0.8rem;color:#6B7280;">
                        {time_range} | {job_addr or 'No address'}
                      </div>
                      <div style="font-size:0.78rem;color:#6B7280;">👷 {crew_names}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with disp_c2:
                st.markdown(f"<div style='padding-top:0.5rem;'>{render_badge(job_status)}</div>", unsafe_allow_html=True)
                if job_addr:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={job_addr.replace(' ','+')}"
                    st.link_button("Get Directions", maps_url, use_container_width=True)
            with disp_c3:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if job_status == "scheduled":
                        if st.button("En Route", key=f"en_route_{entry['id']}", use_container_width=True):
                            try:
                                update_job(job_id, {"status": "in_progress"})
                                st.success("Marked en route!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    elif job_status == "in_progress":
                        if st.button("Arrived", key=f"arrived_{entry['id']}", use_container_width=True):
                            try:
                                create_notification(
                                    user_id, "info",
                                    "Crew arrived",
                                    f"Crew arrived at {job_title}",
                                )
                                st.success("Marked arrived!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                with btn_col2:
                    if st.button("Complete", key=f"complete_{entry['id']}", use_container_width=True):
                        try:
                            update_job(job_id, {"status": "completed", "progress": 100})
                            create_notification(
                                user_id, "success",
                                "Job completed",
                                f"{job_title} marked as completed",
                            )
                            st.success("Job completed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            st.markdown("<hr style='margin:0.25rem 0;border-color:#F3F4F6;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CONFLICT DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab_conflicts:
    st.markdown("### Schedule Conflict Detection")
    st.markdown("Review potential issues with your crew schedule and job assignments.")

    conflicts_found = []

    with st.spinner("Analyzing schedule for conflicts..."):
        # Look ahead 7 days
        check_start = date.today()
        check_end = date.today() + timedelta(days=7)
        try:
            check_schedule = get_schedule(
                company_id,
                date_from=str(check_start),
                date_to=str(check_end),
            )
        except Exception:
            check_schedule = []

        # 1. Double-booking: same crew member on overlapping jobs at same time on same day
        # Build per-day, per-user time blocks
        user_day_slots = {}  # (user_id, date_str) -> list of (start_t, end_t, job_title, entry_id)
        for entry in check_schedule:
            entry_date = entry.get("date", "")
            start_t = entry.get("start_time") or "00:00"
            end_t = entry.get("end_time") or "23:59"
            job_info = entry.get("jobs") or {}
            job_title = job_info.get("title", "Unknown Job")
            try:
                sch_crew = get_crew_for_schedule(entry["id"])
            except Exception:
                sch_crew = []
            for ca in sch_crew:
                uid = ca.get("user_id")
                if uid:
                    key = (uid, entry_date)
                    user_day_slots.setdefault(key, []).append(
                        (start_t, end_t, job_title, entry["id"])
                    )

        # Check for overlaps
        for (uid, entry_date), slots in user_day_slots.items():
            if len(slots) < 2:
                continue
            # Find the user name
            member = next((u for u in all_users if u["id"] == uid), None)
            member_name = member.get("name", "Unknown") if member else "Unknown"

            for i in range(len(slots)):
                for j in range(i + 1, len(slots)):
                    s1_start, s1_end, title1, eid1 = slots[i]
                    s2_start, s2_end, title2, eid2 = slots[j]
                    # Simple overlap check (string comparison works for HH:MM format)
                    if s1_start < s2_end and s2_start < s1_end:
                        conflicts_found.append({
                            "type": "double_booking",
                            "severity": "error",
                            "message": f"**{member_name}** is scheduled for overlapping jobs on {entry_date}:",
                            "detail": f"- {title1} ({s1_start[:5]}–{s1_end[:5]})\n- {title2} ({s2_start[:5]}–{s2_end[:5]})",
                        })

        # 2. Jobs scheduled without crew
        for entry in check_schedule:
            entry_date = entry.get("date", "")
            job_info = entry.get("jobs") or {}
            job_title = job_info.get("title", "Unknown Job")
            try:
                sch_crew = get_crew_for_schedule(entry["id"])
            except Exception:
                sch_crew = []
            if not sch_crew:
                conflicts_found.append({
                    "type": "no_crew",
                    "severity": "warning",
                    "message": f"**{job_title}** scheduled on {entry_date} has no crew assigned.",
                    "detail": "Assign at least one crew member to this job.",
                })

        # 3. Past-due jobs still in 'scheduled' status
        today_str = str(date.today())
        for j in all_jobs:
            if j.get("status") == "scheduled":
                end_d = j.get("end_date") or ""
                if end_d and end_d < today_str:
                    client_name = client_map.get(j.get("client_id",""), {}).get("name","")
                    conflicts_found.append({
                        "type": "past_due",
                        "severity": "warning",
                        "message": f"**{j.get('title','Job')}** ({client_name}) is past its end date ({format_date(end_d)}) but still in 'Scheduled' status.",
                        "detail": "Update the job status or reschedule.",
                        "job_id": j["id"],
                    })

    if not conflicts_found:
        st.markdown(
            """
            <div style="text-align:center;padding:3rem 1rem;background:#F0FDF4;
                        border-radius:12px;border:1px solid #A7F3D0;">
              <div style="font-size:3rem;">✅</div>
              <div style="font-size:1.1rem;font-weight:700;color:#065F46;margin-top:0.75rem;">
                No Conflicts Found
              </div>
              <div style="font-size:0.9rem;color:#047857;margin-top:0.25rem;">
                Your schedule looks clean for the next 7 days.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        errors = [c for c in conflicts_found if c["severity"] == "error"]
        warnings = [c for c in conflicts_found if c["severity"] == "warning"]

        st.markdown(
            f"""
            <div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;">
              <div style="background:#FEE2E2;color:#991B1B;padding:0.5rem 1rem;
                          border-radius:8px;font-weight:600;font-size:0.9rem;">
                🚨 {len(errors)} critical conflict(s)
              </div>
              <div style="background:#FEF3C7;color:#92400E;padding:0.5rem 1rem;
                          border-radius:8px;font-weight:600;font-size:0.9rem;">
                ⚠ {len(warnings)} warning(s)
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for idx, conflict in enumerate(conflicts_found):
            severity = conflict["severity"]
            bg_color = "#FEF2F2" if severity == "error" else "#FFFBEB"
            border_color = "#EF4444" if severity == "error" else "#F59E0B"
            icon = "🚨" if severity == "error" else "⚠"

            st.markdown(
                f"""
                <div style="background:{bg_color};border-left:4px solid {border_color};
                            border-radius:8px;padding:1rem 1.25rem;margin-bottom:0.75rem;">
                  <div style="font-size:1rem;font-weight:700;color:#1F2937;margin-bottom:4px;">
                    {icon} {conflict['message']}
                  </div>
                  <div style="font-size:0.85rem;color:#6B7280;white-space:pre-line;">
                    {conflict['detail']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Resolve action for past-due jobs
            if conflict.get("type") == "past_due" and conflict.get("job_id"):
                jid = conflict["job_id"]
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Mark In Progress", key=f"resolve_ip_{jid}_{idx}"):
                        try:
                            update_job(jid, {"status": "in_progress"})
                            st.success("Status updated to In Progress!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with rc2:
                    if st.button("Mark Completed", key=f"resolve_comp_{jid}_{idx}"):
                        try:
                            update_job(jid, {"status": "completed", "progress": 100})
                            st.success("Job marked complete!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        if st.button("🔄 Re-scan for Conflicts", key="rescan_conflicts"):
            st.rerun()
