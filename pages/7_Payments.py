import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from io import StringIO

from utils.auth import check_authentication, is_role
from utils.styles import inject_css, render_badge, render_page_header, format_currency, format_date, COLORS
from utils.db import (
    create_payment, get_payments_by_company, get_jobs, get_clients, get_client,
    update_payment, log_email,
)
from utils.stripe_integration import create_payment_link, create_invoice, format_amount_for_stripe
from utils.gmail_integration import send_invoice_email

st.set_page_config(page_title="Payments | ServicePro OS", page_icon="💳", layout="wide")

if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()
render_page_header("Payments & Invoicing", "Track revenue and collect payments")

user = st.session_state.user
company = st.session_state.company
company_id = company.get("id", "")

# ── Load all payments ──────────────────────────────────────────────────────────
with st.spinner("Loading payments..."):
    payments = get_payments_by_company(company_id)

# ── Stats computation ──────────────────────────────────────────────────────────
now = datetime.now()
month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

total_revenue = sum(float(p.get("amount", 0) or 0) for p in payments if p.get("status") == "completed")
total_pending = sum(float(p.get("amount", 0) or 0) for p in payments if p.get("status") == "pending")

this_month_revenue = 0.0
this_month_paid_count = 0
for p in payments:
    created_raw = p.get("created_at", "")
    try:
        created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        created_dt = None
    if created_dt and created_dt >= month_start:
        if p.get("status") == "completed":
            this_month_revenue += float(p.get("amount", 0) or 0)
            this_month_paid_count += 1

# ── Top Stats Row ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("💰 Total Revenue", format_currency(total_revenue))
with c2:
    st.metric("⏳ Pending", format_currency(total_pending))
with c3:
    st.metric("📋 This Month Revenue", format_currency(this_month_revenue))
with c4:
    st.metric("✅ Invoices Paid (Month)", str(this_month_paid_count))

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "➕ Create Payment", "📋 Invoice History", "⚙️ Stripe Setup"])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Revenue — Last 6 Months")

    if payments:
        df = pd.DataFrame(payments)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        df_complete = df[df["status"] == "completed"].copy()

        if not df_complete.empty:
            df_complete["month"] = df_complete["created_at"].dt.to_period("M")
            cutoff = pd.Timestamp.now(tz="UTC") - pd.DateOffset(months=6)
            df_recent = df_complete[df_complete["created_at"] >= cutoff]
            monthly = df_recent.groupby("month")["amount"].sum().reset_index()
            monthly["month_str"] = monthly["month"].astype(str)
            monthly = monthly.sort_values("month")
            chart_df = monthly.set_index("month_str")[["amount"]]
            chart_df.columns = ["Revenue ($)"]
            st.bar_chart(chart_df)
        else:
            st.info("No completed payments yet to chart.")

        # Status breakdown
        st.subheader("Payment Status Breakdown")
        bs1, bs2, bs3 = st.columns(3)
        completed_count = len([p for p in payments if p.get("status") == "completed"])
        pending_count = len([p for p in payments if p.get("status") == "pending"])
        failed_count = len([p for p in payments if p.get("status") == "failed"])
        with bs1:
            st.metric("✅ Completed", completed_count)
        with bs2:
            st.metric("⏳ Pending", pending_count)
        with bs3:
            st.metric("❌ Failed", failed_count)
    else:
        st.info("No payment records found. Create your first payment in the Create Payment tab.")

    st.subheader("Recent Payments")

    # Load jobs + clients for lookup
    jobs_list = get_jobs(company_id)
    jobs_map = {j["id"]: j for j in jobs_list}
    clients_list = get_clients(company_id)
    clients_map = {c["id"]: c for c in clients_list}

    recent_payments = payments[:20]
    if recent_payments:
        for p in recent_payments:
            job = jobs_map.get(p.get("job_id", ""), {})
            client = clients_map.get(p.get("client_id", ""), {})
            client_name = client.get("name", "Unknown Client")
            job_title = job.get("title", "No Job")
            amount = float(p.get("amount", 0) or 0)
            status = p.get("status", "pending")
            ptype = (p.get("payment_type") or "invoice").replace("_", " ").title()
            created = format_date(p.get("created_at", "")[:10] if p.get("created_at") else "")
            stripe_link = p.get("stripe_payment_link", "")

            with st.container():
                row_cols = st.columns([2, 2, 2, 1.5, 1.5, 1.5, 3])
                with row_cols[0]:
                    st.write(f"**{created}**")
                with row_cols[1]:
                    st.write(client_name)
                with row_cols[2]:
                    st.write(job_title[:30])
                with row_cols[3]:
                    st.write(f"**{format_currency(amount)}**")
                with row_cols[4]:
                    st.write(ptype)
                with row_cols[5]:
                    st.markdown(render_badge(status), unsafe_allow_html=True)
                with row_cols[6]:
                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        if status != "completed":
                            if st.button("Mark Paid", key=f"mark_paid_{p['id']}", use_container_width=True):
                                with st.spinner("Updating..."):
                                    update_payment(p["id"], {
                                        "status": "completed",
                                        "paid_at": datetime.now().isoformat(),
                                    })
                                st.success("Marked as paid!")
                                st.rerun()
                    with btn_cols[1]:
                        if st.button("Reminder", key=f"remind_{p['id']}", use_container_width=True):
                            client_email = client.get("email", "")
                            if client_email:
                                with st.spinner("Sending reminder..."):
                                    link = stripe_link or "Contact us to pay"
                                    sent = send_invoice_email(
                                        client_email,
                                        client_name,
                                        job_title,
                                        amount,
                                        link,
                                    )
                                if sent:
                                    st.success("Reminder sent!")
                                else:
                                    st.error("Failed to send. Check Gmail settings.")
                            else:
                                st.warning("No email on file for this client.")
                    with btn_cols[2]:
                        if stripe_link:
                            st.markdown(f"[🔗 Invoice]({stripe_link})", unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No recent payments.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — CREATE PAYMENT / INVOICE
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Create New Payment or Invoice")

    jobs_list = get_jobs(company_id)
    active_jobs = [j for j in jobs_list if j.get("status") not in ("completed", "cancelled")]
    job_options = {f"{j['title']} ({j.get('status','').replace('_',' ').title()})": j for j in active_jobs}

    if not job_options:
        st.info("No active jobs found. Create a job first to generate payments.")
    else:
        selected_job_label = st.selectbox("Select Job", list(job_options.keys()), key="pay_job_select")
        selected_job = job_options[selected_job_label]
        job_id = selected_job["id"]
        client_id = selected_job.get("client_id", "")

        # Auto-populate client
        client_data = {}
        if client_id:
            client_data = get_client(client_id) or {}
        client_name = client_data.get("name", "Unknown")
        client_email = client_data.get("email", "")

        col_a, col_b = st.columns(2)
        with col_a:
            st.text_input("Client (auto-filled)", value=client_name, disabled=True)
        with col_b:
            st.text_input("Client Email (auto-filled)", value=client_email, disabled=True)

        # Job total from estimates
        job_total = float(selected_job.get("total", 0) or 0)
        # Try to get total from existing payments context; fallback gracefully
        existing_job_payments = [p for p in payments if p.get("job_id") == job_id and p.get("status") == "completed"]
        already_paid = sum(float(p.get("amount", 0) or 0) for p in existing_job_payments)

        ptype_options = ["Deposit (30%)", "Progress Payment (40%)", "Final Invoice", "Custom Amount"]
        payment_type_label = st.selectbox("Payment Type", ptype_options, key="pay_type")

        # Suggest amount
        if payment_type_label == "Deposit (30%)" and job_total > 0:
            suggested = round(job_total * 0.30, 2)
        elif payment_type_label == "Progress Payment (40%)" and job_total > 0:
            suggested = round(job_total * 0.40, 2)
        elif payment_type_label == "Final Invoice" and job_total > 0:
            suggested = max(0.0, round(job_total - already_paid, 2))
        else:
            suggested = 0.0

        amount = st.number_input(
            "Amount ($)",
            min_value=0.01,
            value=float(suggested) if suggested > 0 else 100.0,
            step=10.0,
            format="%.2f",
            key="pay_amount",
        )

        if suggested > 0:
            st.caption(f"Suggested: {format_currency(suggested)} — Already paid: {format_currency(already_paid)}")

        description = st.text_input(
            "Description",
            value=f"{payment_type_label.split(' (')[0]} — {selected_job['title']}",
            key="pay_desc",
        )
        due_date = st.date_input("Due Date", value=date.today() + timedelta(days=7), key="pay_due")

        st.markdown("---")
        act_col1, act_col2, act_col3 = st.columns(3)

        # ── Stripe Payment Link ────────────────────────────────────────────────
        with act_col1:
            st.markdown("**💳 Online Payment**")
            if st.button("Create Stripe Payment Link", key="create_stripe_link", use_container_width=True):
                stripe_key = company.get("stripe_secret_key", "")
                if not stripe_key:
                    st.warning("Stripe not configured. Go to Settings → API Keys to add your Stripe secret key.")
                else:
                    with st.spinner("Creating Stripe payment link..."):
                        amount_cents = format_amount_for_stripe(amount)
                        link_url = create_payment_link(amount_cents, description, client_email or None)
                    if link_url:
                        st.session_state["last_payment_link"] = link_url
                        st.session_state["last_payment_amount"] = amount
                        st.session_state["last_payment_job_id"] = job_id
                        st.session_state["last_payment_client_id"] = client_id
                        st.session_state["last_payment_desc"] = description
                        # Save to DB
                        create_payment({
                            "company_id": company_id,
                            "job_id": job_id,
                            "client_id": client_id,
                            "amount": amount,
                            "payment_type": payment_type_label.split(" (")[0].lower().replace(" ", "_"),
                            "status": "pending",
                            "stripe_payment_link": link_url,
                            "description": description,
                        })
                        st.success("Stripe payment link created!")

            if st.session_state.get("last_payment_link"):
                link_url = st.session_state["last_payment_link"]
                link_amount = st.session_state.get("last_payment_amount", 0)
                st.markdown("**Payment Link:**")
                st.code(link_url, language=None)
                email_col, _ = st.columns([1, 1])
                with email_col:
                    if st.button("📧 Email Link to Client", key="email_payment_link", use_container_width=True):
                        if client_email:
                            with st.spinner("Sending invoice email..."):
                                sent = send_invoice_email(
                                    client_email, client_name,
                                    selected_job["title"], link_amount, link_url
                                )
                            if sent:
                                st.success(f"Invoice emailed to {client_email}!")
                            else:
                                st.error("Email failed. Check Gmail settings.")
                        else:
                            st.warning("No email on file for this client.")

        # ── Create Invoice ─────────────────────────────────────────────────────
        with act_col2:
            st.markdown("**📄 Stripe Invoice**")
            if st.button("Create Invoice", key="create_invoice_btn", use_container_width=True):
                stripe_key = company.get("stripe_secret_key", "")
                if not stripe_key:
                    st.warning("Stripe not configured. Go to Settings → API Keys.")
                elif not client_email:
                    st.warning("Client has no email address on file.")
                else:
                    with st.spinner("Creating Stripe invoice..."):
                        items = [{"description": description, "amount_cents": format_amount_for_stripe(amount), "quantity": 1}]
                        due_days = (due_date - date.today()).days
                        invoice_result = create_invoice(client_email, client_name, items, max(1, due_days))
                    if invoice_result:
                        invoice_url = invoice_result.get("invoice_url", "")
                        # Save to DB
                        create_payment({
                            "company_id": company_id,
                            "job_id": job_id,
                            "client_id": client_id,
                            "amount": amount,
                            "payment_type": payment_type_label.split(" (")[0].lower().replace(" ", "_"),
                            "status": "pending",
                            "stripe_payment_link": invoice_url,
                            "description": description,
                        })
                        st.success("Invoice created and sent to client via Stripe!")
                        if invoice_url:
                            st.markdown(f"[📄 View Invoice]({invoice_url})", unsafe_allow_html=True)

        # ── Manual Payment ─────────────────────────────────────────────────────
        with act_col3:
            st.markdown("**💵 Manual Payment**")
            with st.form("manual_payment_form"):
                method = st.selectbox("Payment Method", ["Cash", "Check", "Zelle", "Venmo", "Other"])
                ref_num = st.text_input("Reference # (optional)")
                manual_submit = st.form_submit_button("Record Manual Payment", use_container_width=True)

            if manual_submit:
                with st.spinner("Recording payment..."):
                    create_payment({
                        "company_id": company_id,
                        "job_id": job_id,
                        "client_id": client_id,
                        "amount": amount,
                        "payment_type": "manual",
                        "status": "completed",
                        "description": f"{method} payment — {description}" + (f" (Ref: {ref_num})" if ref_num else ""),
                        "paid_at": datetime.now().isoformat(),
                    })
                st.success(f"{method} payment of {format_currency(amount)} recorded!")
                st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — INVOICE HISTORY
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Full Payment History")

    if not payments:
        st.info("No payments recorded yet.")
    else:
        jobs_list2 = get_jobs(company_id)
        jobs_map2 = {j["id"]: j for j in jobs_list2}
        clients_list2 = get_clients(company_id)
        clients_map2 = {c["id"]: c for c in clients_list2}

        # ── Filters ────────────────────────────────────────────────────────────
        f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 2, 2])
        with f1:
            start_filter = st.date_input("From Date", value=date.today() - timedelta(days=90), key="hist_start")
        with f2:
            end_filter = st.date_input("To Date", value=date.today(), key="hist_end")
        with f3:
            status_filter = st.selectbox("Status", ["All", "completed", "pending", "failed"], key="hist_status")
        with f4:
            all_job_titles = ["All"] + list({jobs_map2.get(p.get("job_id", ""), {}).get("title", "Unknown") for p in payments})
            job_filter = st.selectbox("Job", all_job_titles, key="hist_job")
        with f5:
            all_client_names = ["All"] + list({clients_map2.get(p.get("client_id", ""), {}).get("name", "Unknown") for p in payments})
            client_filter = st.selectbox("Client", all_client_names, key="hist_client")

        ptype_filter = st.selectbox("Payment Type", ["All", "deposit", "progress_payment", "final", "manual", "invoice", "custom_amount"], key="hist_type")

        # ── Apply Filters ──────────────────────────────────────────────────────
        filtered = []
        for p in payments:
            created_raw = p.get("created_at", "")
            try:
                p_date = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).date()
            except Exception:
                p_date = date.today()

            if p_date < start_filter or p_date > end_filter:
                continue
            if status_filter != "All" and p.get("status") != status_filter:
                continue
            job = jobs_map2.get(p.get("job_id", ""), {})
            if job_filter != "All" and job.get("title", "Unknown") != job_filter:
                continue
            client = clients_map2.get(p.get("client_id", ""), {})
            if client_filter != "All" and client.get("name", "Unknown") != client_filter:
                continue
            if ptype_filter != "All" and p.get("payment_type") != ptype_filter:
                continue
            filtered.append(p)

        st.caption(f"Showing {len(filtered)} of {len(payments)} payments")

        # ── Table ──────────────────────────────────────────────────────────────
        if filtered:
            rows = []
            for p in filtered:
                job = jobs_map2.get(p.get("job_id", ""), {})
                client = clients_map2.get(p.get("client_id", ""), {})
                rows.append({
                    "Date": format_date(p.get("created_at", "")[:10] if p.get("created_at") else ""),
                    "Client": client.get("name", "—"),
                    "Job": (job.get("title") or "—")[:40],
                    "Amount": format_currency(p.get("amount", 0)),
                    "Type": (p.get("payment_type") or "invoice").replace("_", " ").title(),
                    "Status": (p.get("status") or "pending").title(),
                    "Description": (p.get("description") or "")[:60],
                    "Link": p.get("stripe_payment_link") or "",
                })

            table_df = pd.DataFrame(rows)
            st.dataframe(table_df, use_container_width=True, hide_index=True)

            # ── Export ─────────────────────────────────────────────────────────
            csv_buffer = StringIO()
            table_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            st.download_button(
                "📥 Export CSV",
                data=csv_data,
                file_name=f"payments_{date.today().isoformat()}.csv",
                mime="text/csv",
            )
        else:
            st.info("No payments match the selected filters.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — STRIPE SETUP
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Stripe Integration Setup")

    stripe_secret = company.get("stripe_secret_key", "") or ""
    stripe_pub = company.get("stripe_publishable_key", "") or ""

    if not stripe_secret:
        st.info(
            "To accept online payments, configure your Stripe account in **Settings → API Keys**.\n\n"
            "Stripe allows you to create secure payment links and invoices that clients can pay online with a credit card."
        )
        st.markdown("➡️ [Go to Settings](/10_Settings)")
        st.markdown("""
**Quick Setup:**
1. Create a free account at [stripe.com](https://stripe.com)
2. Go to Developers → API Keys in your Stripe dashboard
3. Copy your Secret Key (starts with `sk_test_` or `sk_live_`)
4. Paste it in Settings → API Keys → Stripe Secret Key
5. Also copy your Publishable Key (starts with `pk_test_` or `pk_live_`)
""")
    else:
        is_test_mode = stripe_secret.startswith("sk_test_")
        mode_label = "🧪 Test Mode" if is_test_mode else "🚀 Live Mode"
        mode_color = "#F59E0B" if is_test_mode else "#10B981"

        st.markdown(
            f'<div style="background:{mode_color}22;border-left:4px solid {mode_color};'
            f'padding:1rem;border-radius:8px;margin-bottom:1rem;">'
            f'<strong>{mode_label}</strong> — Stripe is connected.<br>'
            f'Secret key: <code>{"sk_test_..." if is_test_mode else "sk_live_..."}{"*" * 8}{stripe_secret[-4:]}</code>'
            f"</div>",
            unsafe_allow_html=True,
        )

        if is_test_mode:
            st.warning("You are using Stripe TEST keys. Payments are simulated and no real money moves. Switch to live keys when ready for production.")

        st.markdown(f"[📊 Open Stripe Dashboard](https://dashboard.stripe.com)", unsafe_allow_html=True)

        with st.expander("📡 Webhook Setup (for automatic payment status updates)"):
            st.markdown("""
**To receive automatic payment status updates:**

1. Go to your Stripe Dashboard → Developers → Webhooks
2. Click **"Add endpoint"**
3. Set the endpoint URL to your app's webhook URL:
   ```
   https://your-app-url.streamlit.app/api/stripe-webhook
   ```
4. Select events to listen to:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `invoice.paid`
   - `invoice.payment_failed`
5. Copy the **Webhook Signing Secret** and add it to your Settings

Note: Webhooks require a public HTTPS endpoint. During development, use the Stripe CLI or manually mark payments as paid in the app.
""")

        with st.expander("🔑 Update Stripe Keys"):
            st.markdown("To update your Stripe keys, go to [Settings → API Keys](/10_Settings).")
