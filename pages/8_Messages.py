import streamlit as st
from datetime import datetime, timezone

from utils.auth import check_authentication, is_role
from utils.styles import inject_css, render_page_header, COLORS
from utils.db import (
    send_message, get_conversation, get_all_conversations,
    mark_messages_read, get_unread_count,
    get_users_by_company, get_jobs,
)
from utils.gmail_integration import send_email, get_recent_emails

st.set_page_config(page_title="Messages | ServicePro OS", page_icon="💬", layout="wide")

if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()
render_page_header("Messages", "Communicate with clients and crew")

user = st.session_state.user
company = st.session_state.company
company_id = company.get("id", "")
user_id = user.get("id", "")

# ── Helper: relative time ──────────────────────────────────────────────────────
def relative_time(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        elif seconds < 172800:
            return "Yesterday"
        else:
            return dt.strftime("%b %d")
    except Exception:
        return ""


# ── Helper: colored initials avatar ───────────────────────────────────────────
def avatar_html(name: str, size: int = 36) -> str:
    initials = "".join(w[0].upper() for w in (name or "?").split()[:2])
    colors = ["#10B981", "#3B82F6", "#8B5CF6", "#F59E0B", "#EF4444", "#06B6D4"]
    color = colors[hash(name) % len(colors)]
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};'
        f'color:white;display:inline-flex;align-items:center;justify-content:center;'
        f'font-weight:700;font-size:{max(10, size//3)}px;flex-shrink:0;">{initials}</div>'
    )


# ── Session state defaults ─────────────────────────────────────────────────────
if "selected_conversation" not in st.session_state:
    st.session_state.selected_conversation = None  # dict with other_user_id, other_name, job_id
if "message_tab" not in st.session_state:
    st.session_state.message_tab = "inapp"
if "show_new_message" not in st.session_state:
    st.session_state.show_new_message = False
if "selected_email" not in st.session_state:
    st.session_state.selected_email = None

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading messages..."):
    conversations = get_all_conversations(company_id, user_id)
    company_users = get_users_by_company(company_id)
    jobs_list = get_jobs(company_id)

users_map = {u["id"]: u for u in company_users}
jobs_map = {j["id"]: j for j in jobs_list}

# ── New Message Modal ──────────────────────────────────────────────────────────
if st.session_state.show_new_message:
    st.markdown("### ✏️ New Message")
    with st.form("new_message_form"):
        other_users = [u for u in company_users if u["id"] != user_id]
        if not other_users:
            st.warning("No other users in your company to message.")
            st.form_submit_button("Close")
            st.session_state.show_new_message = False
        else:
            user_options = {f"{u['name']} ({u.get('role','').title()})": u for u in other_users}
            selected_user_label = st.selectbox("Send To", list(user_options.keys()))
            selected_recipient = user_options[selected_user_label]

            job_options = {"No specific job": None}
            for j in jobs_list:
                job_options[j["title"]] = j["id"]
            job_label = st.selectbox("Related Job (optional)", list(job_options.keys()))
            related_job_id = job_options[job_label]

            context_note = st.text_input("Subject / Context (optional)")
            new_msg_content = st.text_area("Message", height=100, placeholder="Type your message...")

            col_send, col_cancel = st.columns([1, 1])
            with col_send:
                submitted = st.form_submit_button("Send Message", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                if new_msg_content.strip():
                    full_content = new_msg_content.strip()
                    if context_note.strip():
                        full_content = f"[{context_note.strip()}] {full_content}"
                    with st.spinner("Sending..."):
                        send_message({
                            "company_id": company_id,
                            "sender_id": user_id,
                            "recipient_id": selected_recipient["id"],
                            "content": full_content,
                            "job_id": related_job_id,
                        })
                    st.session_state.selected_conversation = {
                        "other_user_id": selected_recipient["id"],
                        "other_name": selected_recipient["name"],
                        "other_role": selected_recipient.get("role", ""),
                        "job_id": related_job_id,
                    }
                    st.session_state.show_new_message = False
                    st.rerun()
                else:
                    st.warning("Message cannot be empty.")
            if cancelled:
                st.session_state.show_new_message = False
                st.rerun()

    st.markdown("---")

# ── Two-column layout ──────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2])

# ────────────────────────────────────────────────────────────────────────
# LEFT PANEL — Conversation List
# ────────────────────────────────────────────────────────────────────────
with left_col:
    tab_inapp, tab_email = st.tabs(["💬 In-App", "📧 Email"])

    # ── In-App Conversations ──────────────────────────────────────────────
    with tab_inapp:
        st.session_state.message_tab = "inapp"

        if st.button("✏️ New Message", use_container_width=True, key="new_msg_btn"):
            st.session_state.show_new_message = True
            st.rerun()

        unread_total = get_unread_count(user_id)
        if unread_total > 0:
            st.markdown(f'<div style="color:#3B82F6;font-size:0.85rem;margin-bottom:0.5rem;">🔵 {unread_total} unread message(s)</div>', unsafe_allow_html=True)

        if not conversations:
            st.markdown(
                '<div style="text-align:center;padding:2rem;color:#9CA3AF;">'
                '<div style="font-size:2rem;">💬</div>'
                '<div style="margin-top:0.5rem;">No conversations yet</div>'
                '<div style="font-size:0.8rem;">Start a new message above</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            for thread in conversations:
                sender_id = thread.get("sender_id", "")
                recipient_id = thread.get("recipient_id", "")
                other_id = recipient_id if sender_id == user_id else sender_id
                other_user = users_map.get(other_id, {})
                other_name = other_user.get("name", "Unknown User")
                other_role = other_user.get("role", "")
                is_unread = not thread.get("is_read", True) and thread.get("recipient_id") == user_id
                content_preview = (thread.get("content") or "")[:50]
                if len(thread.get("content") or "") > 50:
                    content_preview += "..."
                ts = relative_time(thread.get("created_at", ""))
                related_job = jobs_map.get(thread.get("job_id", ""), {})

                selected = (
                    st.session_state.selected_conversation is not None
                    and st.session_state.selected_conversation.get("other_user_id") == other_id
                )
                bg = "#EFF6FF" if selected else "white"
                border = "2px solid #3B82F6" if selected else "1px solid #E5E7EB"

                conv_html = (
                    f'<div style="background:{bg};border:{border};border-radius:10px;'
                    f'padding:0.75rem;margin-bottom:0.5rem;cursor:pointer;">'
                    f'<div style="display:flex;align-items:center;gap:0.6rem;">'
                    f'{avatar_html(other_name, 36)}'
                    f'<div style="flex:1;min-width:0;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<span style="font-weight:{"700" if is_unread else "600"};font-size:0.9rem;">{other_name}</span>'
                    f'<span style="font-size:0.75rem;color:#9CA3AF;">{ts}</span>'
                    f'</div>'
                    f'<div style="font-size:0.8rem;color:#6B7280;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                    f'{"🔵 " if is_unread else ""}{content_preview}'
                    f'</div>'
                    + (f'<div style="font-size:0.75rem;color:#10B981;margin-top:2px;">📋 {related_job.get("title","")}</div>' if related_job else "")
                    + "</div></div></div>"
                )
                st.markdown(conv_html, unsafe_allow_html=True)

                if st.button(
                    f"Open chat with {other_name}",
                    key=f"conv_{other_id}",
                    use_container_width=True,
                    help=f"Open conversation with {other_name}",
                ):
                    st.session_state.selected_conversation = {
                        "other_user_id": other_id,
                        "other_name": other_name,
                        "other_role": other_role,
                        "job_id": thread.get("job_id"),
                    }
                    st.session_state.message_tab = "inapp"
                    st.rerun()

    # ── Email Tab ─────────────────────────────────────────────────────────
    with tab_email:
        st.session_state.message_tab = "email"

        if st.button("✉️ Compose Email", use_container_width=True, key="compose_email_btn"):
            st.session_state.selected_conversation = None
            st.session_state.selected_email = None

        gmail_configured = bool(company.get("gmail_email") and company.get("gmail_app_password"))

        if not gmail_configured:
            st.info("Gmail not configured. Go to Settings → API Keys to connect your Gmail account.")
        else:
            with st.spinner("Loading recent emails..."):
                try:
                    recent_emails = get_recent_emails(limit=20)
                except Exception:
                    recent_emails = []

            if not recent_emails:
                st.info("No recent emails found in your inbox.")
            else:
                for i, em in enumerate(recent_emails):
                    from_addr = em.get("from", "")[:30]
                    subject = em.get("subject", "(No Subject)")[:40]
                    preview = em.get("body_preview", "")[:60]
                    em_date = em.get("date", "")[:16]

                    selected_em = st.session_state.selected_email == i
                    bg_em = "#EFF6FF" if selected_em else "white"

                    em_html = (
                        f'<div style="background:{bg_em};border:1px solid #E5E7EB;border-radius:8px;'
                        f'padding:0.6rem;margin-bottom:0.4rem;">'
                        f'<div style="font-weight:600;font-size:0.85rem;">{subject}</div>'
                        f'<div style="font-size:0.75rem;color:#6B7280;">From: {from_addr}</div>'
                        f'<div style="font-size:0.75rem;color:#9CA3AF;">{em_date}</div>'
                        f'<div style="font-size:0.8rem;color:#6B7280;margin-top:4px;">{preview}</div>'
                        f'</div>'
                    )
                    st.markdown(em_html, unsafe_allow_html=True)
                    if st.button(f"Read", key=f"read_email_{i}", use_container_width=True):
                        st.session_state.selected_email = i
                        st.session_state.selected_email_data = em
                        st.session_state.message_tab = "email"
                        st.rerun()

# ────────────────────────────────────────────────────────────────────────
# RIGHT PANEL — Message Thread / Email Compose
# ────────────────────────────────────────────────────────────────────────
with right_col:
    active_tab = st.session_state.message_tab

    # ── In-App Thread ─────────────────────────────────────────────────────
    if active_tab == "inapp":
        if st.session_state.selected_conversation is None:
            st.markdown(
                '<div style="display:flex;align-items:center;justify-content:center;'
                'height:400px;flex-direction:column;color:#9CA3AF;">'
                '<div style="font-size:4rem;">💬</div>'
                '<div style="font-size:1.2rem;font-weight:600;color:#374151;margin-top:1rem;">Select a conversation</div>'
                '<div style="font-size:0.9rem;margin-top:0.5rem;">Choose a chat from the left or start a new message</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            conv = st.session_state.selected_conversation
            other_id = conv["other_user_id"]
            other_name = conv["other_name"]
            other_role = conv.get("other_role", "")
            job_id = conv.get("job_id")

            # Chat header
            header_job = jobs_map.get(job_id or "", {})
            job_label = f" — 📋 {header_job['title']}" if header_job else ""

            hc1, hc2 = st.columns([3, 2])
            with hc1:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;">'
                    f'{avatar_html(other_name, 44)}'
                    f'<div><div style="font-weight:700;font-size:1.1rem;">{other_name}</div>'
                    f'<div style="font-size:0.8rem;color:#6B7280;">{other_role.title()}{job_label}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with hc2:
                action_c1, action_c2, action_c3 = st.columns(3)
                other_user_data = users_map.get(other_id, {})
                with action_c1:
                    other_phone = other_user_data.get("phone", "")
                    if other_phone:
                        st.markdown(f"[📞 Call](tel:{other_phone})", unsafe_allow_html=True)
                    else:
                        st.write("📞 —")
                with action_c2:
                    if header_job:
                        st.markdown("📍 [View Job](/5_Jobs)", unsafe_allow_html=True)
                    else:
                        st.write("📍 —")
                with action_c3:
                    other_email = other_user_data.get("email", "")
                    if other_email:
                        st.markdown(f"[📧 Email](mailto:{other_email})", unsafe_allow_html=True)
                    else:
                        st.write("📧 —")

            st.markdown("---")

            # Load + mark read
            with st.spinner("Loading messages..."):
                thread_messages = get_conversation(user_id, other_id, job_id)
                mark_messages_read(user_id, other_id)

            # Render chat bubbles
            if not thread_messages:
                st.markdown(
                    '<div style="text-align:center;padding:2rem;color:#9CA3AF;">'
                    'No messages yet. Send the first one below!'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                chat_html = '<div style="max-height:400px;overflow-y:auto;padding:0.5rem 0;">'
                for msg in thread_messages:
                    is_mine = msg.get("sender_id") == user_id
                    content = msg.get("content", "")
                    ts = relative_time(msg.get("created_at", ""))
                    sender_name = user["name"] if is_mine else other_name

                    if is_mine:
                        chat_html += (
                            f'<div style="display:flex;justify-content:flex-end;margin:0.5rem 0;">'
                            f'<div style="max-width:70%;">'
                            f'<div class="chat-message-user">{content}</div>'
                            f'<div class="chat-timestamp" style="text-align:right;">{ts}</div>'
                            f'</div></div>'
                        )
                    else:
                        chat_html += (
                            f'<div style="display:flex;justify-content:flex-start;margin:0.5rem 0;gap:0.5rem;">'
                            f'{avatar_html(sender_name, 28)}'
                            f'<div style="max-width:70%;">'
                            f'<div class="chat-message-other">{content}</div>'
                            f'<div class="chat-timestamp">{ts}</div>'
                            f'</div></div>'
                        )
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)

            # Message input
            st.markdown("---")
            msg_col, send_col = st.columns([5, 1])
            with msg_col:
                new_text = st.text_input(
                    "Message",
                    placeholder="Type a message...",
                    label_visibility="collapsed",
                    key="msg_input_field",
                )
            with send_col:
                send_clicked = st.button("Send →", use_container_width=True, key="send_msg_btn")

            if send_clicked and new_text.strip():
                with st.spinner("Sending..."):
                    send_message({
                        "company_id": company_id,
                        "sender_id": user_id,
                        "recipient_id": other_id,
                        "content": new_text.strip(),
                        "job_id": job_id,
                    })
                st.rerun()

    # ── Email Panel ───────────────────────────────────────────────────────
    elif active_tab == "email":
        gmail_configured = bool(company.get("gmail_email") and company.get("gmail_app_password"))

        if not gmail_configured:
            st.warning("Gmail is not configured. Go to Settings → API Keys to set up email sending.")
        else:
            # Show selected email if any
            if st.session_state.get("selected_email_data"):
                em_data = st.session_state.selected_email_data
                st.markdown(f"### 📧 {em_data.get('subject', '(No Subject)')}")
                st.markdown(f"**From:** {em_data.get('from', '')}")
                st.markdown(f"**Date:** {em_data.get('date', '')}")
                st.markdown("---")
                st.text_area("Message Body", value=em_data.get("body_preview", "(Preview not available)"), height=200, disabled=True)
                if st.button("← Back to Compose"):
                    st.session_state.selected_email_data = None
                    st.session_state.selected_email = None
                    st.rerun()
            else:
                st.subheader("✉️ Compose Email")

                # Pre-fill from selected conversation
                conv = st.session_state.selected_conversation
                prefill_to = ""
                if conv:
                    other_user = users_map.get(conv.get("other_user_id", ""), {})
                    prefill_to = other_user.get("email", "")

                with st.form("compose_email_form"):
                    to_addr = st.text_input("To", value=prefill_to, placeholder="recipient@example.com")
                    cc_addr = st.text_input("CC (optional)", placeholder="cc@example.com")
                    subject_line = st.text_input("Subject", placeholder="Subject of your email")
                    body_text = st.text_area(
                        "Message",
                        height=250,
                        placeholder="Write your message here...\n\nYou can include:\n- Plain text\n- Line breaks for formatting",
                    )
                    attachment = st.file_uploader("Attach PDF (optional)", type=["pdf"])
                    send_email_btn = st.form_submit_button("Send Email", use_container_width=True)

                if send_email_btn:
                    if not to_addr.strip():
                        st.error("Please enter a recipient email address.")
                    elif not subject_line.strip():
                        st.error("Please enter a subject.")
                    elif not body_text.strip():
                        st.error("Please write a message body.")
                    else:
                        attachments = []
                        if attachment:
                            attachments = [(attachment.name, attachment.read())]
                        cc_list = [a.strip() for a in cc_addr.split(",") if a.strip()] if cc_addr else None
                        # Convert plain text to simple HTML
                        body_html = body_text.replace("\n", "<br>")
                        with st.spinner("Sending email..."):
                            sent_ok = send_email(
                                to_email=to_addr.strip(),
                                subject=subject_line.strip(),
                                body_html=body_html,
                                attachments=attachments if attachments else None,
                                cc=cc_list,
                            )
                        if sent_ok:
                            st.success(f"Email sent to {to_addr}!")
                        else:
                            st.error("Failed to send email. Check your Gmail settings in Settings → API Keys.")
