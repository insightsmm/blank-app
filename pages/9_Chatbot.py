import streamlit as st

from utils.auth import check_authentication
from utils.styles import inject_css, render_page_header, COLORS
from utils.db import get_jobs, get_estimates, get_clients, get_dashboard_stats
from utils.claude_ai import chat_with_context

st.set_page_config(page_title="AI Assistant | ServicePro OS", page_icon="🤖", layout="wide")

if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()

user = st.session_state.user
company = st.session_state.company
company_id = company.get("id", "")
user_name = user.get("name", "there")
user_role = user.get("role", "crew")

# ── Initialize chat history ────────────────────────────────────────────────────
if "chatbot_messages" not in st.session_state:
    st.session_state.chatbot_messages = [
        {
            "role": "assistant",
            "content": (
                f"Hi {user_name}! I'm your ServicePro AI Assistant. "
                f"I can help you with estimates, job management, scheduling, payments, client communication, and more. "
                f"What can I help you with today?"
            ),
        }
    ]

if "chatbot_input_value" not in st.session_state:
    st.session_state.chatbot_input_value = ""

# ── Quick action pre-fills ─────────────────────────────────────────────────────
QUICK_ACTIONS = {
    "📝 Estimate Help": "Help me create a professional estimate for an interior painting job. What information should I collect from the client?",
    "📅 Schedule Help": "How should I schedule my crew efficiently for multiple jobs this week? What's the best approach?",
    "💰 Revenue Report": "Give me advice on how to analyze my revenue and identify my most profitable service types.",
    "✉️ Draft Email": "Help me draft a professional follow-up email for a client whose proposal has been pending for a week.",
}

SUGGESTION_PROMPTS = [
    "What's my revenue this month?",
    "Help me write an estimate for interior painting",
    "Which crew members are available tomorrow?",
    "Draft a follow-up email for a pending proposal",
    "What are my top clients by revenue?",
    "Suggest pricing for a 2000 sqft painting job",
]

# ── Layout: left sidebar (1/4) + right chat (3/4) ─────────────────────────────
left_col, right_col = st.columns([1, 3])

# ────────────────────────────────────────────────────────────────────────
# LEFT COLUMN — Assistant Info + Quick Actions
# ────────────────────────────────────────────────────────────────────────
with left_col:
    st.markdown(
        """
        <div style="background:white;border-radius:16px;padding:1.5rem;
             border:1px solid #E5E7EB;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
          <div style="text-align:center;margin-bottom:1rem;">
            <div style="font-size:2.5rem;">🤖</div>
            <div style="font-weight:800;font-size:1.1rem;color:#1F2937;margin-top:0.5rem;">
              ServicePro AI Assistant
            </div>
            <div style="font-size:0.8rem;color:#6B7280;margin-top:0.25rem;">
              Powered by Claude
            </div>
          </div>
          <div style="font-size:0.85rem;color:#374151;line-height:1.6;border-top:1px solid #F3F4F6;padding-top:1rem;">
            Your intelligent business assistant. Ask me anything about:
            <ul style="margin:0.5rem 0;padding-left:1.2rem;color:#6B7280;">
              <li>Creating estimates</li>
              <li>Managing jobs</li>
              <li>Scheduling crew</li>
              <li>Payment questions</li>
              <li>Business insights</li>
              <li>Client communication</li>
            </ul>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**⚡ Quick Actions**")

    for label, prompt_text in QUICK_ACTIONS.items():
        if st.button(label, use_container_width=True, key=f"quick_{label}"):
            st.session_state.chatbot_input_value = prompt_text
            st.rerun()

    st.markdown("---")

    if st.button("🗑 Clear Chat", use_container_width=True, key="clear_chat"):
        st.session_state.chatbot_messages = [
            {
                "role": "assistant",
                "content": (
                    f"Chat cleared! Hi again, {user_name}. How can I help you today?"
                ),
            }
        ]
        st.session_state.chatbot_input_value = ""
        st.rerun()

    # AI config status
    anthropic_key = company.get("anthropic_key", "")
    if anthropic_key:
        st.markdown(
            '<div style="background:#D1FAE5;border-radius:8px;padding:0.5rem;'
            'text-align:center;font-size:0.8rem;color:#065F46;margin-top:0.5rem;">'
            '✅ AI Connected'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#FEE2E2;border-radius:8px;padding:0.5rem;'
            'text-align:center;font-size:0.8rem;color:#991B1B;margin-top:0.5rem;">'
            '❌ Add Anthropic Key in Settings'
            '</div>',
            unsafe_allow_html=True,
        )

# ────────────────────────────────────────────────────────────────────────
# RIGHT COLUMN — Chat Interface
# ────────────────────────────────────────────────────────────────────────
with right_col:
    render_page_header("AI Assistant", "Ask anything about your business")

    # ── Chat history display ───────────────────────────────────────────────
    chat_container = st.container()

    with chat_container:
        msgs = st.session_state.chatbot_messages

        if len(msgs) <= 1:
            # Show suggestion chips when chat is essentially empty
            st.markdown("**💡 Try asking:**")
            chip_row1 = st.columns(3)
            chip_row2 = st.columns(3)
            for i, prompt_text in enumerate(SUGGESTION_PROMPTS):
                row = chip_row1 if i < 3 else chip_row2
                col_idx = i % 3
                with row[col_idx]:
                    if st.button(prompt_text, key=f"suggestion_{i}", use_container_width=True):
                        st.session_state.chatbot_input_value = prompt_text
                        st.rerun()
            st.markdown("---")

        # Render all messages as chat bubbles
        bubble_html = '<div style="max-height:500px;overflow-y:auto;padding:0.5rem;">'
        for msg in msgs:
            role = msg.get("role", "user")
            content = msg.get("content", "").replace("\n", "<br>")
            if role == "user":
                bubble_html += (
                    f'<div style="display:flex;justify-content:flex-end;margin:0.75rem 0;">'
                    f'<div style="max-width:75%;">'
                    f'<div class="chat-message-user">{content}</div>'
                    f'<div class="chat-timestamp" style="text-align:right;">You</div>'
                    f'</div>'
                    f'<div style="width:36px;height:36px;border-radius:50%;background:#3B82F6;'
                    f'color:white;display:inline-flex;align-items:center;justify-content:center;'
                    f'font-weight:700;font-size:14px;flex-shrink:0;margin-left:8px;">You</div>'
                    f'</div>'
                )
            else:
                bubble_html += (
                    f'<div style="display:flex;justify-content:flex-start;margin:0.75rem 0;gap:0.5rem;">'
                    f'<div style="width:36px;height:36px;border-radius:50%;background:#10B981;'
                    f'color:white;display:inline-flex;align-items:center;justify-content:center;'
                    f'font-size:18px;flex-shrink:0;">🤖</div>'
                    f'<div style="max-width:75%;">'
                    f'<div class="chat-message-other">{content}</div>'
                    f'<div class="chat-timestamp">ServicePro AI</div>'
                    f'</div>'
                    f'</div>'
                )
        bubble_html += '</div>'
        st.markdown(bubble_html, unsafe_allow_html=True)

    # ── Input row ─────────────────────────────────────────────────────────
    st.markdown("---")
    input_col, send_col = st.columns([5, 1])

    with input_col:
        user_input = st.text_input(
            "Message",
            value=st.session_state.chatbot_input_value,
            placeholder="Message ServicePro AI...",
            label_visibility="collapsed",
            key="chatbot_input_field",
        )
    with send_col:
        send_btn = st.button("Send →", use_container_width=True, key="chatbot_send_btn")

    # Determine if we should process a message
    should_send = send_btn and user_input.strip()

    # Also handle pre-filled quick actions
    if st.session_state.chatbot_input_value and not send_btn:
        # Pre-filled value from quick action — auto-trigger on next render
        user_input = st.session_state.chatbot_input_value

    if should_send or (st.session_state.chatbot_input_value and send_btn):
        final_input = user_input.strip()
        if final_input:
            # Add user message to history
            st.session_state.chatbot_messages.append({
                "role": "user",
                "content": final_input,
            })
            st.session_state.chatbot_input_value = ""

            # ── Special command handling ───────────────────────────────────
            lower_input = final_input.lower()

            inline_data = ""
            if "show my jobs" in lower_input or "list my jobs" in lower_input:
                with st.spinner("Fetching jobs..."):
                    all_jobs = get_jobs(company_id)
                active_jobs = [j for j in all_jobs if j.get("status") in ("scheduled", "in_progress")]
                if active_jobs:
                    job_lines = "\n".join(
                        f"- {j['title']} ({j.get('status','').replace('_',' ')})" for j in active_jobs[:10]
                    )
                    inline_data = f"\n\n[Live data from your account]\nActive jobs:\n{job_lines}"
                else:
                    inline_data = "\n\n[Live data: No active jobs currently.]"

            # ── Build context ──────────────────────────────────────────────
            with st.spinner("Fetching business context..."):
                try:
                    stats = get_dashboard_stats(company_id)
                    active_jobs_count = stats.get("active_jobs", 0)
                    open_estimates_count = stats.get("open_estimates", 0)
                    total_clients_count = stats.get("total_clients", 0)
                    revenue_this_month = stats.get("revenue_this_month", 0.0)
                except Exception:
                    active_jobs_count = 0
                    open_estimates_count = 0
                    total_clients_count = 0
                    revenue_this_month = 0.0

            company_context = {
                "name": company.get("name", "Your Company"),
                "trade_types": company.get("trade_types", ["painting", "electrical", "landscaping"]),
                "active_jobs": active_jobs_count,
                "open_estimates": open_estimates_count,
                "total_clients": total_clients_count,
                "revenue_this_month": f"${revenue_this_month:,.2f}",
            }

            # Build history for Claude (last 10 turns, excluding current)
            history_for_claude = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.chatbot_messages[:-1][-10:]
            ]

            augmented_input = final_input + inline_data

            # ── Handle special link suggestions ──────────────────────────
            suggestion_suffix = ""
            if "create estimate" in lower_input or "new estimate" in lower_input:
                suggestion_suffix = "\n\n[Tip: You can create an estimate at the Estimates page.]"
            elif "schedule" in lower_input and ("view" in lower_input or "show" in lower_input or "open" in lower_input):
                suggestion_suffix = "\n\n[Tip: View and manage your schedule at the Schedule page.]"

            # ── Call Claude ────────────────────────────────────────────────
            with st.spinner("Thinking..."):
                response_text = chat_with_context(
                    augmented_input,
                    history_for_claude,
                    company_context,
                    user_role,
                )

            if suggestion_suffix:
                response_text = response_text + suggestion_suffix

            st.session_state.chatbot_messages.append({
                "role": "assistant",
                "content": response_text,
            })

            st.rerun()
