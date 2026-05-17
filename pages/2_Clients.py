import streamlit as st
from datetime import datetime

from utils.auth import check_authentication, is_role
from utils.styles import (
    inject_css,
    render_badge,
    render_page_header,
    format_currency,
    format_date,
    render_metric_card,
    COLORS,
)
from utils.db import (
    get_clients,
    get_client,
    create_client,
    update_client,
    delete_client,
    get_estimates_by_client,
    get_jobs_by_client,
    get_email_log,
    get_unread_notifications_count,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clients | ServicePro OS",
    page_icon="👥",
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

# ── Session state defaults ────────────────────────────────────────────────────
if "client_view" not in st.session_state:
    st.session_state.client_view = "list"   # "list" | "detail" | "add" | "edit"
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = None
if "client_search" not in st.session_state:
    st.session_state.client_search = ""
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "client_edit_mode" not in st.session_state:
    st.session_state.client_edit_mode = False

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

    if st.session_state.client_view != "list":
        st.markdown("---")
        if st.button("← Back to Client List", use_container_width=True):
            st.session_state.client_view = "list"
            st.session_state.selected_client_id = None
            st.session_state.show_add_form = False
            st.session_state.client_edit_mode = False
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# GEOCODE helper (graceful fallback)
# ─────────────────────────────────────────────────────────────────────────────
def try_geocode(address, city, state, zip_code):
    try:
        from utils.maps import geocode_address
        result = geocode_address(address, city, state, zip_code)
        if result:
            return result.get("lat"), result.get("lng")
    except Exception:
        pass
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# GMAIL send helper (graceful fallback)
# ─────────────────────────────────────────────────────────────────────────────
def try_send_email(to_email, subject, body):
    try:
        from utils.gmail_integration import send_email
        gmail_email = company.get("gmail_email", "")
        gmail_pass = company.get("gmail_app_password", "")
        if not gmail_email or not gmail_pass:
            return False, "Gmail not configured in company settings."
        result = send_email(
            gmail_email=gmail_email,
            gmail_app_password=gmail_pass,
            to_email=to_email,
            subject=subject,
            body=body,
        )
        return True, "Email sent successfully."
    except Exception as exc:
        return False, str(exc)


# ─────────────────────────────────────────────────────────────────────────────
# ── VIEW: LIST ────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
def render_list_view():
    render_page_header("👥 Clients", "Manage your client relationships")

    # ── Top bar ───────────────────────────────────────────────────────────────
    top_l, top_r = st.columns([3, 1])
    with top_l:
        search_term = st.text_input(
            "🔍 Search clients...",
            value=st.session_state.client_search,
            key="client_search_input",
            placeholder="Search by name, email, or phone…",
        )
        st.session_state.client_search = search_term
    with top_r:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add New Client", use_container_width=True, key="open_add_form"):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.rerun()

    # ── Add Client Form ───────────────────────────────────────────────────────
    if st.session_state.show_add_form:
        with st.expander("➕ New Client", expanded=True):
            with st.form("add_client_form", clear_on_submit=True):
                st.markdown("#### Client Information")
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    new_name = st.text_input("Full Name *", key="new_name")
                with fc2:
                    new_email = st.text_input("Email", key="new_email")
                with fc3:
                    new_phone = st.text_input("Phone", key="new_phone")

                fa1, fa2, fa3, fa4 = st.columns([3, 2, 1, 1])
                with fa1:
                    new_address = st.text_input("Street Address", key="new_address")
                with fa2:
                    new_city = st.text_input("City", key="new_city")
                with fa3:
                    new_state = st.text_input("State", key="new_state", max_chars=2)
                with fa4:
                    new_zip = st.text_input("ZIP", key="new_zip")

                new_notes = st.text_area("Notes", key="new_notes", height=80)
                new_tags = st.text_input("Tags (comma-separated)", key="new_tags",
                                         placeholder="vip, commercial, referral")

                btn_save, btn_cancel = st.columns(2)
                with btn_save:
                    submitted = st.form_submit_button("💾 Save Client", use_container_width=True)
                with btn_cancel:
                    cancelled = st.form_submit_button("Cancel", use_container_width=True)

                if cancelled:
                    st.session_state.show_add_form = False
                    st.rerun()

                if submitted:
                    if not new_name.strip():
                        st.error("Client name is required.")
                    else:
                        lat, lng = try_geocode(new_address, new_city, new_state, new_zip)
                        tags_list = [t.strip() for t in new_tags.split(",") if t.strip()]
                        payload = {
                            "company_id": company_id,
                            "name": new_name.strip(),
                            "email": new_email.strip() or None,
                            "phone": new_phone.strip() or None,
                            "address": new_address.strip() or None,
                            "city": new_city.strip() or None,
                            "state": new_state.strip().upper() or None,
                            "zip": new_zip.strip() or None,
                            "lat": lat,
                            "lng": lng,
                            "notes": new_notes.strip() or None,
                            "tags": tags_list,
                        }
                        created = create_client(payload)
                        if created:
                            st.success(f"✅ Client '{new_name}' added successfully!")
                            st.session_state.show_add_form = False
                            st.rerun()
                        else:
                            st.error("Failed to create client. Please try again.")

    # ── Load clients ──────────────────────────────────────────────────────────
    clients = get_clients(company_id, search=st.session_state.client_search or None)

    if not clients:
        if st.session_state.client_search:
            st.info(f"No clients matching '{st.session_state.client_search}'.")
        else:
            st.markdown(
                """
                <div style="text-align:center;padding:4rem 1rem;color:#9CA3AF;
                            background:white;border-radius:12px;border:1px solid #F3F4F6;margin-top:1rem;">
                  <div style="font-size:3rem;">👥</div>
                  <div style="font-size:1.2rem;font-weight:700;color:#374151;margin-top:0.5rem;">No clients yet</div>
                  <div style="font-size:0.9rem;margin-top:0.25rem;">Add your first client using the button above.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    st.markdown(f"**{len(clients)} client{'s' if len(clients) != 1 else ''}** found")
    st.markdown("---")

    # ── Client rows ────────────────────────────────────────────────────────────
    for client in clients:
        cid = client["id"]
        name = client.get("name", "Unnamed")
        email = client.get("email", "—")
        phone = client.get("phone", "—")
        address_parts = [
            p for p in [
                client.get("address"),
                client.get("city"),
                client.get("state"),
                client.get("zip"),
            ] if p
        ]
        address_str = ", ".join(address_parts) if address_parts else "—"
        notes = client.get("notes", "") or ""
        tags = client.get("tags", []) or []

        with st.container():
            r1, r2, r3, r4, r5 = st.columns([3, 2, 2, 3, 2])
            with r1:
                # Name + tags
                tags_html = " ".join(
                    f'<span style="background:#DBEAFE;color:#1E40AF;padding:2px 8px;'
                    f'border-radius:12px;font-size:11px;font-weight:600;">{t}</span>'
                    for t in tags[:3]
                )
                st.markdown(
                    f'<div style="font-weight:700;color:#1F2937;">{name}</div>'
                    f'<div style="font-size:0.82rem;color:#6B7280;">{tags_html}</div>',
                    unsafe_allow_html=True,
                )
            with r2:
                st.markdown(
                    f'<div style="font-size:0.85rem;color:#374151;">📧 {email}</div>'
                    f'<div style="font-size:0.85rem;color:#374151;">📞 {phone}</div>',
                    unsafe_allow_html=True,
                )
            with r3:
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#6B7280;">📍 {address_str[:40]}{"…" if len(address_str) > 40 else ""}</div>',
                    unsafe_allow_html=True,
                )
            with r4:
                if notes:
                    st.markdown(
                        f'<div style="font-size:0.82rem;color:#9CA3AF;font-style:italic;">{notes[:60]}{"…" if len(notes) > 60 else ""}</div>',
                        unsafe_allow_html=True,
                    )
            with r5:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("View", key=f"view_{cid}", use_container_width=True):
                        st.session_state.selected_client_id = cid
                        st.session_state.client_view = "detail"
                        st.session_state.client_edit_mode = False
                        st.rerun()
                with btn_col2:
                    if st.button("Edit", key=f"edit_{cid}", use_container_width=True):
                        st.session_state.selected_client_id = cid
                        st.session_state.client_view = "detail"
                        st.session_state.client_edit_mode = True
                        st.rerun()

            st.markdown('<div style="border-bottom:1px solid #F3F4F6;margin:4px 0;"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ── VIEW: DETAIL ──────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
def render_detail_view():
    client_id = st.session_state.selected_client_id
    client = get_client(client_id)

    if not client:
        st.error("Client not found.")
        if st.button("← Back to Clients"):
            st.session_state.client_view = "list"
            st.rerun()
        return

    name = client.get("name", "Unknown")
    email = client.get("email", "")
    phone = client.get("phone", "")
    address_parts = [
        p for p in [
            client.get("address"),
            client.get("city"),
            client.get("state"),
            client.get("zip"),
        ] if p
    ]
    address_str = ", ".join(address_parts) if address_parts else ""

    render_page_header(f"👤 {name}", "Client Profile")

    # ── Back button + edit toggle ─────────────────────────────────────────────
    hdr_l, hdr_r = st.columns([6, 1])
    with hdr_l:
        if st.button("← Back to Clients", key="back_from_detail"):
            st.session_state.client_view = "list"
            st.session_state.selected_client_id = None
            st.session_state.client_edit_mode = False
            st.rerun()
    with hdr_r:
        if not st.session_state.client_edit_mode:
            if st.button("✏️ Edit Client", key="toggle_edit"):
                st.session_state.client_edit_mode = True
                st.rerun()

    # ── Client Header Card ────────────────────────────────────────────────────
    maps_key = company.get("google_maps_key", "")
    maps_link = f"https://www.google.com/maps/search/?api=1&query={address_str.replace(' ', '+')}" if address_str else "#"

    st.markdown(
        f"""
        <div class="card" style="display:flex;align-items:flex-start;gap:1.5rem;">
          <div style="font-size:3.5rem;line-height:1;">👤</div>
          <div style="flex:1;">
            <div style="font-size:1.5rem;font-weight:800;color:#1F2937;">{name}</div>
            {"" if not email else f'<div style="color:#6B7280;font-size:0.9rem;">📧 <a href="mailto:{email}" style="color:#3B82F6;">{email}</a></div>'}
            {"" if not phone else f'<div style="color:#6B7280;font-size:0.9rem;">📞 {phone}</div>'}
            {"" if not address_str else f'<div style="color:#6B7280;font-size:0.9rem;">📍 <a href="{maps_link}" target="_blank" style="color:#3B82F6;">{address_str}</a></div>'}
          </div>
          <div>{render_badge("client")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 4 Tabs ────────────────────────────────────────────────────────────────
    tab_overview, tab_estimates, tab_jobs, tab_comms = st.tabs(
        ["📋 Overview", "📝 Estimates", "🔨 Jobs", "📧 Communications"]
    )

    # ─── TAB 1: Overview ──────────────────────────────────────────────────────
    with tab_overview:
        # Quick stats
        estimates = get_estimates_by_client(client_id)
        jobs = get_jobs_by_client(client_id)
        total_spent = sum(float(e.get("total", 0) or 0) for e in estimates if e.get("status") == "approved")
        open_estimates = sum(1 for e in estimates if e.get("status") in ("draft", "sent"))

        qs1, qs2, qs3 = st.columns(3)
        with qs1:
            st.markdown(
                render_metric_card("Total Jobs", len(jobs), icon="🔨"),
                unsafe_allow_html=True,
            )
        with qs2:
            st.markdown(
                render_metric_card("Total Spent", format_currency(total_spent), icon="💰"),
                unsafe_allow_html=True,
            )
        with qs3:
            st.markdown(
                render_metric_card("Open Estimates", open_estimates, icon="📝"),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Edit form or display
        if st.session_state.client_edit_mode:
            st.markdown("#### ✏️ Edit Client Information")
            with st.form("edit_client_form"):
                ef1, ef2, ef3 = st.columns(3)
                with ef1:
                    edit_name = st.text_input("Full Name *", value=client.get("name", ""))
                with ef2:
                    edit_email = st.text_input("Email", value=client.get("email", "") or "")
                with ef3:
                    edit_phone = st.text_input("Phone", value=client.get("phone", "") or "")

                ea1, ea2, ea3, ea4 = st.columns([3, 2, 1, 1])
                with ea1:
                    edit_address = st.text_input("Street Address", value=client.get("address", "") or "")
                with ea2:
                    edit_city = st.text_input("City", value=client.get("city", "") or "")
                with ea3:
                    edit_state = st.text_input("State", value=client.get("state", "") or "", max_chars=2)
                with ea4:
                    edit_zip = st.text_input("ZIP", value=client.get("zip", "") or "")

                edit_notes = st.text_area("Notes", value=client.get("notes", "") or "", height=100)
                existing_tags = client.get("tags", []) or []
                edit_tags = st.text_input(
                    "Tags (comma-separated)",
                    value=", ".join(existing_tags),
                )

                save_btn, cancel_btn = st.columns(2)
                with save_btn:
                    save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
                with cancel_btn:
                    cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

                if cancel_clicked:
                    st.session_state.client_edit_mode = False
                    st.rerun()

                if save_clicked:
                    if not edit_name.strip():
                        st.error("Name is required.")
                    else:
                        lat, lng = try_geocode(edit_address, edit_city, edit_state, edit_zip)
                        tags_list = [t.strip() for t in edit_tags.split(",") if t.strip()]
                        updated = update_client(client_id, {
                            "name": edit_name.strip(),
                            "email": edit_email.strip() or None,
                            "phone": edit_phone.strip() or None,
                            "address": edit_address.strip() or None,
                            "city": edit_city.strip() or None,
                            "state": edit_state.strip().upper() or None,
                            "zip": edit_zip.strip() or None,
                            "lat": lat,
                            "lng": lng,
                            "notes": edit_notes.strip() or None,
                            "tags": tags_list,
                        })
                        if updated:
                            st.success("✅ Client updated!")
                            st.session_state.client_edit_mode = False
                            st.rerun()
                        else:
                            st.error("Update failed. Please try again.")
        else:
            # Display contact info
            st.markdown("#### 📇 Contact Information")
            ci1, ci2 = st.columns(2)
            with ci1:
                st.markdown(
                    f"""
                    <div class="card">
                      <div style="font-size:0.82rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Email</div>
                      <div style="font-weight:600;color:#1F2937;">{email or "—"}</div>
                      <div style="margin-top:0.75rem;font-size:0.82rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Phone</div>
                      <div style="font-weight:600;color:#1F2937;">{phone or "—"}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with ci2:
                tags_html = " ".join(
                    f'<span style="background:#DBEAFE;color:#1E40AF;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;">{t}</span>'
                    for t in (client.get("tags", []) or [])
                ) or "—"
                st.markdown(
                    f"""
                    <div class="card">
                      <div style="font-size:0.82rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Address</div>
                      <div style="font-weight:600;color:#1F2937;">{address_str or "—"}</div>
                      <div style="margin-top:0.75rem;font-size:0.82rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Tags</div>
                      <div style="margin-top:4px;">{tags_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if client.get("notes"):
                st.markdown("#### 📓 Notes")
                st.markdown(
                    f'<div class="card" style="color:#374151;">{client["notes"]}</div>',
                    unsafe_allow_html=True,
                )

        # Danger zone
        st.markdown("<br>", unsafe_allow_html=True)
        if is_role("owner", "admin"):
            with st.expander("⚠️ Danger Zone"):
                st.warning("Deleting a client is permanent and cannot be undone.")
                confirm_del = st.checkbox(f"I confirm I want to delete '{name}'")
                if st.button("🗑️ Delete Client", disabled=not confirm_del, key="delete_client_btn"):
                    ok = delete_client(client_id)
                    if ok:
                        st.success("Client deleted.")
                        st.session_state.client_view = "list"
                        st.session_state.selected_client_id = None
                        st.rerun()
                    else:
                        st.error("Failed to delete client.")

    # ─── TAB 2: Estimates ────────────────────────────────────────────────────
    with tab_estimates:
        TRADE_ICONS = {"painting": "🎨", "electrical": "⚡", "landscaping": "🌿"}
        estimates = get_estimates_by_client(client_id)

        est_header_l, est_header_r = st.columns([4, 1])
        with est_header_r:
            if st.button(f"➕ New Estimate", key="new_est_for_client", use_container_width=True):
                st.session_state.estimate_preset_client_id = client_id
                st.switch_page("pages/3_Estimates.py")

        if not estimates:
            st.markdown(
                """
                <div style="text-align:center;padding:3rem;color:#9CA3AF;">
                  <div style="font-size:2.5rem;">📝</div>
                  <div style="font-weight:700;color:#374151;margin-top:0.5rem;">No estimates yet</div>
                  <div style="font-size:0.9rem;">Create an estimate for this client to get started.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for est in estimates:
                eid = est["id"]
                trade = est.get("trade_type", "")
                trade_icon = TRADE_ICONS.get(trade, "🏠")
                trade_label = f"{trade_icon} {trade.title()}"
                total = format_currency(est.get("total", 0))
                badge = render_badge(est.get("status", "draft"))
                date_str = format_date(est.get("created_at", ""))
                short_id = str(eid)[:8].upper()

                with st.expander(f"#{short_id} — {trade_label} — {total} — {date_str}"):
                    ed1, ed2, ed3 = st.columns(3)
                    with ed1:
                        st.markdown(f"**Status:** {badge}", unsafe_allow_html=True)
                        st.markdown(f"**Total:** {total}")
                    with ed2:
                        subtotal = format_currency(est.get("subtotal", 0))
                        tax = format_currency(est.get("tax", 0))
                        discount = format_currency(est.get("discount", 0))
                        st.markdown(f"**Subtotal:** {subtotal}")
                        st.markdown(f"**Tax:** {tax}")
                        st.markdown(f"**Discount:** {discount}")
                    with ed3:
                        valid_until = est.get("valid_until", "")
                        st.markdown(f"**Valid Until:** {format_date(valid_until) if valid_until else '—'}")
                        st.markdown(f"**Created:** {date_str}")

                    line_items = est.get("line_items", []) or []
                    if line_items:
                        st.markdown("**Line Items:**")
                        for li in line_items:
                            st.markdown(
                                f"- {li.get('description', '')} — Qty: {li.get('qty', 1)} × "
                                f"{format_currency(li.get('unit_price', 0))} = **{format_currency(li.get('total', 0))}**"
                            )

                    act1, act2, act3 = st.columns(3)
                    with act1:
                        if st.button("📄 Download PDF", key=f"pdf_{eid}"):
                            try:
                                from utils.pdf_generator import generate_proposal_pdf
                                pdf_bytes = generate_proposal_pdf(est, client, company, line_items)
                                st.download_button(
                                    "📥 Download",
                                    pdf_bytes,
                                    f"proposal_{short_id}.pdf",
                                    "application/pdf",
                                    key=f"dl_{eid}",
                                )
                            except Exception as exc:
                                st.error(f"PDF generation failed: {exc}")
                    with act2:
                        if st.button("📧 Send to Client", key=f"send_est_{eid}"):
                            if not email:
                                st.warning("Client has no email address.")
                            else:
                                try:
                                    from utils.gmail_integration import send_proposal_email
                                    gmail_email = company.get("gmail_email", "")
                                    gmail_pass = company.get("gmail_app_password", "")
                                    if not gmail_email:
                                        st.warning("Gmail not configured.")
                                    else:
                                        send_proposal_email(
                                            gmail_email=gmail_email,
                                            gmail_app_password=gmail_pass,
                                            client=client,
                                            estimate=est,
                                            company=company,
                                        )
                                        from utils.db import update_estimate
                                        update_estimate(eid, {"status": "sent", "sent_at": datetime.utcnow().isoformat()})
                                        st.success("✅ Proposal sent!")
                                        st.rerun()
                                except Exception as exc:
                                    st.error(f"Send failed: {exc}")
                    with act3:
                        if est.get("status") == "sent":
                            if st.button("✅ Mark Approved", key=f"approve_{eid}"):
                                from utils.db import update_estimate
                                update_estimate(eid, {"status": "approved", "approved_at": datetime.utcnow().isoformat()})
                                st.success("Marked as approved.")
                                st.rerun()

    # ─── TAB 3: Jobs ─────────────────────────────────────────────────────────
    with tab_jobs:
        jobs = get_jobs_by_client(client_id)

        if not jobs:
            st.markdown(
                """
                <div style="text-align:center;padding:3rem;color:#9CA3AF;">
                  <div style="font-size:2.5rem;">🔨</div>
                  <div style="font-weight:700;color:#374151;margin-top:0.5rem;">No jobs yet</div>
                  <div style="font-size:0.9rem;">Jobs will appear here once estimates are converted.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for job in jobs:
                jid = job["id"]
                jtitle = job.get("title", "Untitled Job")
                jstatus = job.get("status", "scheduled")
                jprogress = int(job.get("progress", 0) or 0)
                jstart = format_date(job.get("start_date", ""))
                jend = format_date(job.get("end_date", ""))
                date_range = f"{jstart} → {jend}" if jstart and jend else jstart or jend or "—"

                with st.container():
                    jc1, jc2, jc3, jc4 = st.columns([3, 2, 3, 1])
                    with jc1:
                        st.markdown(f"**{jtitle}**")
                        badge = render_badge(jstatus)
                        st.markdown(badge, unsafe_allow_html=True)
                    with jc2:
                        st.markdown(f"**Progress:** {jprogress}%")
                        st.progress(jprogress / 100)
                    with jc3:
                        st.markdown(f"📅 {date_range}")
                    with jc4:
                        if st.button("View", key=f"view_job_{jid}"):
                            st.info(f"Job detail view coming soon (Job ID: {str(jid)[:8]})")

                    st.markdown('<div style="border-bottom:1px solid #F3F4F6;margin:6px 0;"></div>', unsafe_allow_html=True)

    # ─── TAB 4: Communications ───────────────────────────────────────────────
    with tab_comms:
        # Email log
        st.markdown("#### 📬 Email History")
        try:
            email_logs = get_email_log(company_id, limit=20)
            client_emails = [
                e for e in email_logs
                if e.get("to_email", "").lower() == (email or "").lower()
            ]

            if not client_emails:
                st.markdown(
                    '<div style="color:#9CA3AF;padding:1rem;">No emails sent to this client yet.</div>',
                    unsafe_allow_html=True,
                )
            else:
                for log_entry in client_emails:
                    subj = log_entry.get("subject", "(no subject)")
                    log_status = log_entry.get("status", "sent")
                    log_date = format_date(log_entry.get("created_at", ""))
                    badge = render_badge(log_status)
                    st.markdown(
                        f"""
                        <div style="padding:0.6rem;border-bottom:1px solid #F3F4F6;display:flex;justify-content:space-between;align-items:center;">
                          <div>
                            <span style="font-weight:600;">{subj}</span>
                            <span style="margin-left:8px;">{badge}</span>
                          </div>
                          <div style="font-size:0.8rem;color:#9CA3AF;">{log_date}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        except Exception as exc:
            st.warning(f"Could not load email log: {exc}")

        st.markdown("---")
        st.markdown("#### ✉️ Send Email")
        if not email:
            st.warning("This client has no email address on file. Edit the client to add one.")
        else:
            with st.form("send_email_form"):
                email_subject = st.text_input("Subject", placeholder="e.g. Your estimate is ready")
                email_body = st.text_area(
                    "Message",
                    height=150,
                    placeholder="Dear {client_name},\n\nThank you for choosing us...",
                )
                send_btn = st.form_submit_button("📧 Send Email", use_container_width=True)

                if send_btn:
                    if not email_subject.strip() or not email_body.strip():
                        st.error("Subject and message are required.")
                    else:
                        ok, msg = try_send_email(email, email_subject, email_body)
                        if ok:
                            st.success(f"✅ {msg}")
                            # Log the email
                            try:
                                from utils.db import log_email
                                log_email({
                                    "company_id": company_id,
                                    "from_email": company.get("gmail_email", ""),
                                    "to_email": email,
                                    "subject": email_subject,
                                    "body": email_body,
                                    "status": "sent",
                                })
                            except Exception:
                                pass
                            st.rerun()
                        else:
                            st.error(f"Failed to send: {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# ── ROUTER ───────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
view = st.session_state.client_view

if view == "list":
    render_list_view()
elif view == "detail":
    render_detail_view()
else:
    render_list_view()
