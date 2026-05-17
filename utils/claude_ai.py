import anthropic
import streamlit as st
import json
from typing import List, Dict, Optional, Generator

SYSTEM_PROMPT = """You are the ServicePro OS AI Assistant, helping field service professionals manage their business.
You help with: creating estimates, managing jobs, scheduling crews, answering client questions, and business advice.
Be concise, professional, and actionable. Focus on painting, electrical, and landscaping services."""

CLIENT_SYSTEM_PROMPT = """You are a friendly customer service assistant for a professional field service company.
You help clients with: job status updates, appointment scheduling, proposal questions, and general inquiries.
Be warm, professional, and helpful. If you don't know something specific about their job, let them know a team member will follow up."""


def get_client() -> Optional[anthropic.Anthropic]:
    """Return an Anthropic client using the company's API key, or None."""
    try:
        company = st.session_state.get("company", {}) or {}
        api_key = company.get("anthropic_key", "")
        if not api_key:
            return None
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        print(f"get_client error: {e}")
        return None


def chat_with_assistant(
    messages: List[Dict],
    system_prompt: str = None,
) -> str:
    """
    Send a list of {role, content} messages to Claude and return the text response.
    Uses claude-opus-4-7. Returns an error message string on failure.
    """
    client = get_client()
    if not client:
        return "AI Assistant is not configured. Please add your Anthropic API key in Settings."

    try:
        system = system_prompt or SYSTEM_PROMPT
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        return response.content[0].text if response.content else ""
    except anthropic.AuthenticationError:
        return "Invalid Anthropic API key. Please update it in Settings."
    except anthropic.RateLimitError:
        return "Rate limit reached. Please wait a moment and try again."
    except Exception as e:
        print(f"chat_with_assistant error: {e}")
        return f"AI Assistant error: {str(e)}"


def get_estimate_ai_suggestions(
    trade_type: str,
    inputs: dict,
    current_estimate: dict,
) -> dict:
    """
    Analyze an estimate and return AI-driven suggestions.
    Returns: {recommendations: [], upsells: [], price_adjustment: float, summary: str}
    """
    default = {
        "recommendations": [],
        "upsells": [],
        "price_adjustment": 0.0,
        "summary": "",
    }

    client = get_client()
    if not client:
        return default

    try:
        total = float(current_estimate.get("total", 0) or 0)
        prompt = (
            f"I am preparing a {trade_type} service estimate.\n"
            f"Project inputs: {json.dumps(inputs, default=str)}\n"
            f"Current estimate total: ${total:,.2f}\n"
            f"Current line items: {json.dumps(current_estimate.get('line_items', []), default=str)}\n\n"
            f"Please analyze this estimate and respond ONLY with a valid JSON object "
            f"(no markdown, no code fences) matching exactly this structure:\n"
            f'{{"recommendations": ["string", ...], "upsells": ["string", ...], '
            f'"price_adjustment": 0.0, "summary": "string"}}\n'
            f"price_adjustment is a dollar amount (positive or negative) to suggest adjusting the total."
        )

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip() if response.content else "{}"
        # Strip any accidental markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        return {
            "recommendations": result.get("recommendations", []),
            "upsells": result.get("upsells", []),
            "price_adjustment": float(result.get("price_adjustment", 0)),
            "summary": result.get("summary", ""),
        }
    except json.JSONDecodeError as e:
        print(f"get_estimate_ai_suggestions JSON error: {e}")
        return default
    except Exception as e:
        print(f"get_estimate_ai_suggestions error: {e}")
        return default


def generate_job_summary(
    job: dict,
    crew: list,
    media_count: int,
    progress: int,
) -> str:
    """Auto-generate a professional job progress summary for a given job."""
    client = get_client()
    if not client:
        return "AI summary unavailable — Anthropic API key not configured."

    try:
        crew_names = ", ".join(c.get("users", {}).get("name", "Unknown") for c in crew) if crew else "Not assigned"
        prompt = (
            f"Generate a professional job progress summary (2-3 sentences) for:\n"
            f"Job: {job.get('title', 'Untitled')}\n"
            f"Trade: {job.get('trade_type', 'service').title()}\n"
            f"Status: {job.get('status', 'unknown').replace('_', ' ')}\n"
            f"Progress: {progress}%\n"
            f"Crew: {crew_names}\n"
            f"Photos on file: {media_count}\n"
            f"Notes: {job.get('notes', 'None')}\n\n"
            f"Write a concise, professional summary suitable for sharing with a client."
        )

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip() if response.content else ""
    except Exception as e:
        print(f"generate_job_summary error: {e}")
        return "Unable to generate summary at this time."


def analyze_photo_description(job_title: str, trade_type: str) -> str:
    """
    Generate a description prompt/guideline for field photos for a given job.
    Returns a short instructional string for the field crew.
    """
    client = get_client()
    if not client:
        return f"Upload photos showing progress on: {job_title}"

    try:
        prompt = (
            f"For a {trade_type} job titled '{job_title}', write a short (1-2 sentences) "
            f"instruction for field crew on what photos to capture to best document this job. "
            f"Be specific to {trade_type} work."
        )
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip() if response.content else f"Document progress for: {job_title}"
    except Exception as e:
        print(f"analyze_photo_description error: {e}")
        return f"Upload photos showing progress on: {job_title}"


def generate_proposal_description(
    trade_type: str,
    inputs: dict,
    line_items: list,
) -> str:
    """
    Write a professional 'Scope of Work' section for a proposal PDF.
    Returns a multi-paragraph string.
    """
    client = get_client()
    if not client:
        return f"Professional {trade_type} services as itemized in the estimate above."

    try:
        items_text = "\n".join(
            f"- {item.get('description', '')}: ${float(item.get('total', 0) or 0):,.2f}"
            for item in (line_items or [])
        )
        prompt = (
            f"Write a professional 'Scope of Work' section for a {trade_type} service proposal.\n"
            f"Project details: {json.dumps(inputs, default=str)}\n"
            f"Line items:\n{items_text}\n\n"
            f"Write 2-3 paragraphs that professionally describe the scope of work, "
            f"quality standards, and what the client can expect. "
            f"Do not include pricing — that's in the table."
        )
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=768,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip() if response.content else ""
    except Exception as e:
        print(f"generate_proposal_description error: {e}")
        return f"Professional {trade_type} services as itemized in this proposal."


def chat_with_context(
    user_message: str,
    chat_history: List[Dict],
    company_context: dict,
    user_role: str,
) -> str:
    """
    Context-aware chatbot that includes company info and user role in the system prompt.
    chat_history: list of {role, content} dicts (prior turns)
    Returns the assistant's response as a string.
    """
    client = get_client()
    if not client:
        return "AI Assistant is not configured. Please add your Anthropic API key in Settings."

    try:
        company_name = company_context.get("name", "the company")
        trade_types = company_context.get("trade_types", ["painting", "electrical", "landscaping"])
        if isinstance(trade_types, str):
            import json as _json
            try:
                trade_types = _json.loads(trade_types)
            except Exception:
                trade_types = [trade_types]

        system = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Current context:\n"
            f"- Company: {company_name}\n"
            f"- Services offered: {', '.join(str(t) for t in trade_types)}\n"
            f"- User role: {user_role}\n\n"
            f"You have access to information about clients, jobs, estimates, scheduling, "
            f"payments, and crew management. Help the user with their specific question or task. "
            f"If you need data you don't have, suggest where in the app to find it."
        )

        # Build messages list (history + new message)
        messages = list(chat_history) + [{"role": "user", "content": user_message}]

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text.strip() if response.content else ""

    except anthropic.AuthenticationError:
        return "Invalid Anthropic API key. Please update it in Settings."
    except anthropic.RateLimitError:
        return "Rate limit reached. Please wait a moment and try again."
    except Exception as e:
        print(f"chat_with_context error: {e}")
        return f"I encountered an error: {str(e)}"


def stream_chat_response(
    user_message: str,
    chat_history: List[Dict],
    system_prompt: str = None,
) -> Generator[str, None, None]:
    """
    Stream a Claude response token-by-token.
    Use with st.write_stream() for live typewriter output.

    Usage in a page:
        with st.chat_message("assistant"):
            response = st.write_stream(
                stream_chat_response(user_input, history)
            )
        # response is the full accumulated string after streaming
    """
    client = get_client()
    if not client:
        yield "AI chat is not configured. Please add your Anthropic API key in Settings → API Keys."
        return

    try:
        messages = list(chat_history) + [{"role": "user", "content": user_message}]
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=system_prompt or SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.AuthenticationError:
        yield "Invalid Anthropic API key. Please update it in Settings."
    except anthropic.RateLimitError:
        yield "Rate limit reached — please wait a moment and try again."
    except Exception as e:
        print(f"stream_chat_response error: {e}")
        yield f"Error: {str(e)}"


def stream_client_chat(
    user_message: str,
    chat_history: List[Dict],
    company_name: str,
    job_context: dict = None,
) -> Generator[str, None, None]:
    """
    Streaming chat for client-facing conversations (from the Messages page).
    Includes job/company context so Claude can answer client questions.
    """
    client = get_client()
    if not client:
        yield "Chat is currently unavailable. Please contact us directly."
        return

    try:
        job_info = ""
        if job_context:
            job_info = (
                f"\nCurrent job context: {job_context.get('title', 'N/A')}, "
                f"Status: {job_context.get('status', 'N/A')}, "
                f"Progress: {job_context.get('progress', 0)}%"
            )

        system = (
            f"{CLIENT_SYSTEM_PROMPT}\n\n"
            f"You are representing: {company_name}\n"
            f"{job_info}\n"
            f"Keep responses concise and client-friendly."
        )

        messages = list(chat_history) + [{"role": "user", "content": user_message}]
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=512,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        print(f"stream_client_chat error: {e}")
        yield "I'm having trouble responding right now. Please try again."


def stream_with_context(
    user_message: str,
    chat_history: List[Dict],
    company_context: dict,
    user_role: str,
) -> Generator[str, None, None]:
    """
    Streaming version of chat_with_context — for the AI Assistant page.
    Yields tokens as they arrive from Claude.
    """
    client = get_client()
    if not client:
        yield "AI Assistant is not configured. Please add your Anthropic API key in Settings."
        return

    try:
        company_name = company_context.get("name", "the company")
        trade_types = company_context.get("trade_types", ["painting", "electrical", "landscaping"])
        if isinstance(trade_types, str):
            try:
                trade_types = json.loads(trade_types)
            except Exception:
                trade_types = [trade_types]

        system = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Current context:\n"
            f"- Company: {company_name}\n"
            f"- Services: {', '.join(str(t) for t in trade_types)}\n"
            f"- User role: {user_role}\n\n"
            f"Help the user with their specific question. If you need data you don't have, "
            f"suggest where in the app to find it."
        )

        messages = list(chat_history) + [{"role": "user", "content": user_message}]
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.AuthenticationError:
        yield "Invalid Anthropic API key. Please update it in Settings."
    except anthropic.RateLimitError:
        yield "Rate limit reached. Please wait a moment and try again."
    except Exception as e:
        print(f"stream_with_context error: {e}")
        yield f"Error: {str(e)}"
