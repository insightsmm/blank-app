import streamlit as st
from supabase import create_client, Client
import bcrypt
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

SCHEMA_SQL = """
-- Run this in Supabase SQL editor to set up the database
CREATE TABLE IF NOT EXISTS companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'My Company',
    email TEXT, phone TEXT, address TEXT, website TEXT, logo_url TEXT,
    stripe_secret_key TEXT, stripe_publishable_key TEXT,
    gmail_email TEXT, gmail_app_password TEXT,
    google_maps_key TEXT, anthropic_key TEXT,
    claude_chat_enabled BOOLEAN DEFAULT TRUE,
    trade_types JSONB DEFAULT '["painting","electrical","landscaping"]',
    pricing_config JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'crew',
    phone TEXT, avatar_url TEXT, is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS clients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL, email TEXT, phone TEXT,
    address TEXT, city TEXT, state TEXT, zip TEXT,
    lat DOUBLE PRECISION, lng DOUBLE PRECISION,
    notes TEXT, tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS estimates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id),
    created_by UUID REFERENCES users(id),
    trade_type TEXT NOT NULL,
    inputs JSONB DEFAULT '{}', line_items JSONB DEFAULT '[]',
    subtotal DECIMAL(10,2) DEFAULT 0, tax DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) DEFAULT 0, total DECIMAL(10,2) DEFAULT 0,
    status TEXT DEFAULT 'draft',
    notes TEXT, valid_until DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(), sent_at TIMESTAMPTZ, approved_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS proposals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    estimate_id UUID REFERENCES estimates(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'draft',
    sent_at TIMESTAMPTZ, signed_at TIMESTAMPTZ, signature_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id),
    estimate_id UUID REFERENCES estimates(id),
    title TEXT NOT NULL, description TEXT, trade_type TEXT,
    address TEXT, city TEXT, state TEXT, zip TEXT,
    lat DOUBLE PRECISION, lng DOUBLE PRECISION,
    status TEXT DEFAULT 'scheduled',
    progress INTEGER DEFAULT 0,
    start_date DATE, end_date DATE, notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS schedule (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    date DATE NOT NULL, start_time TIME, end_time TIME,
    notes TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS crew_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id UUID REFERENCES schedule(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id),
    user_id UUID REFERENCES users(id),
    role TEXT DEFAULT 'crew',
    status TEXT DEFAULT 'assigned',
    check_in_time TIMESTAMPTZ, check_out_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS job_media (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES users(id),
    filename TEXT, storage_path TEXT, media_type TEXT DEFAULT 'photo',
    caption TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    job_id UUID REFERENCES jobs(id),
    client_id UUID REFERENCES clients(id),
    amount DECIMAL(10,2) NOT NULL,
    payment_type TEXT DEFAULT 'invoice',
    status TEXT DEFAULT 'pending',
    stripe_payment_intent_id TEXT, stripe_payment_link TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(), paid_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    sender_id UUID REFERENCES users(id),
    recipient_id UUID REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    content TEXT NOT NULL, is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS email_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    from_email TEXT, to_email TEXT, subject TEXT, body TEXT,
    status TEXT DEFAULT 'sent', error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'info', title TEXT NOT NULL, content TEXT,
    is_read BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def get_supabase() -> Optional[Client]:
    """Gets from st.session_state or creates new Supabase client."""
    if "supabase" in st.session_state and st.session_state.supabase is not None:
        return st.session_state.supabase
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        client = create_client(url, key)
        st.session_state.supabase = client
        return client
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return None


# ─── USERS ───────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch a user record by email address."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("users").select("*").eq("email", email).single().execute()
        return result.data
    except Exception as e:
        print(f"get_user_by_email error: {e}")
        return None


def create_user(data: dict) -> Optional[Dict]:
    """Create a new user, hashing the password if provided."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        payload = dict(data)
        if "password" in payload:
            raw = payload.pop("password")
            payload["password_hash"] = bcrypt.hashpw(
                raw.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        result = sb.table("users").insert(payload).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_user error: {e}")
        return None


def get_users_by_company(company_id: str) -> List[Dict]:
    """Get all users belonging to a company."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("users")
            .select("*")
            .eq("company_id", company_id)
            .order("name")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_users_by_company error: {e}")
        return []


def get_user(user_id: str) -> Optional[Dict]:
    """Fetch a single user by ID."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("users").select("*").eq("id", user_id).single().execute()
        return result.data
    except Exception as e:
        print(f"get_user error: {e}")
        return None


def update_user(user_id: str, data: dict) -> Optional[Dict]:
    """Update user fields."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        payload = dict(data)
        if "password" in payload:
            raw = payload.pop("password")
            payload["password_hash"] = bcrypt.hashpw(
                raw.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        result = sb.table("users").update(payload).eq("id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_user error: {e}")
        return None


# ─── COMPANIES ───────────────────────────────────────────────────────────────

def get_company(company_id: str) -> Optional[Dict]:
    """Fetch a company by ID."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("companies").select("*").eq("id", company_id).single().execute()
        return result.data
    except Exception as e:
        print(f"get_company error: {e}")
        return None


def create_company(data: dict) -> Optional[Dict]:
    """Create a new company record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("companies").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_company error: {e}")
        return None


def update_company(company_id: str, data: dict) -> Optional[Dict]:
    """Update company fields."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("companies").update(data).eq("id", company_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_company error: {e}")
        return None


# ─── CLIENTS ─────────────────────────────────────────────────────────────────

def get_clients(company_id: str, search: str = None) -> List[Dict]:
    """Fetch all clients for a company, optionally filtered by search string."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        query = sb.table("clients").select("*").eq("company_id", company_id).order("name")
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,email.ilike.%{search}%,phone.ilike.%{search}%"
            )
        result = query.execute()
        return result.data or []
    except Exception as e:
        print(f"get_clients error: {e}")
        return []


def get_client(client_id: str) -> Optional[Dict]:
    """Fetch a single client by ID."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("clients").select("*").eq("id", client_id).single().execute()
        return result.data
    except Exception as e:
        print(f"get_client error: {e}")
        return None


def create_client(data: dict) -> Optional[Dict]:
    """Create a new client record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("clients").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_client error: {e}")
        return None


def update_client(client_id: str, data: dict) -> Optional[Dict]:
    """Update client fields."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("clients").update(data).eq("id", client_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_client error: {e}")
        return None


def delete_client(client_id: str) -> bool:
    """Delete a client record."""
    try:
        sb = get_supabase()
        if not sb:
            return False
        sb.table("clients").delete().eq("id", client_id).execute()
        return True
    except Exception as e:
        print(f"delete_client error: {e}")
        return False


# ─── ESTIMATES ───────────────────────────────────────────────────────────────

def create_estimate(data: dict) -> Optional[Dict]:
    """Create a new estimate record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("estimates").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_estimate error: {e}")
        return None


def get_estimate(estimate_id: str) -> Optional[Dict]:
    """Fetch a single estimate by ID."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("estimates").select("*").eq("id", estimate_id).single().execute()
        return result.data
    except Exception as e:
        print(f"get_estimate error: {e}")
        return None


def get_estimates(company_id: str, status: str = None, trade_type: str = None) -> List[Dict]:
    """Fetch estimates for a company with optional filters."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        query = (
            sb.table("estimates")
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
        )
        if status:
            query = query.eq("status", status)
        if trade_type:
            query = query.eq("trade_type", trade_type)
        result = query.execute()
        return result.data or []
    except Exception as e:
        print(f"get_estimates error: {e}")
        return []


def get_estimates_by_client(client_id: str) -> List[Dict]:
    """Fetch all estimates for a specific client."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("estimates")
            .select("*")
            .eq("client_id", client_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_estimates_by_client error: {e}")
        return []


def update_estimate(estimate_id: str, data: dict) -> Optional[Dict]:
    """Update estimate fields."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("estimates").update(data).eq("id", estimate_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_estimate error: {e}")
        return None


# ─── PROPOSALS ───────────────────────────────────────────────────────────────

def create_proposal(data: dict) -> Optional[Dict]:
    """Create a new proposal record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("proposals").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_proposal error: {e}")
        return None


def get_proposal_by_estimate(estimate_id: str) -> Optional[Dict]:
    """Fetch the proposal associated with an estimate."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = (
            sb.table("proposals")
            .select("*")
            .eq("estimate_id", estimate_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"get_proposal_by_estimate error: {e}")
        return None


def update_proposal(proposal_id: str, data: dict) -> Optional[Dict]:
    """Update proposal fields."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("proposals").update(data).eq("id", proposal_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_proposal error: {e}")
        return None


# ─── JOBS ────────────────────────────────────────────────────────────────────

def create_job(data: dict) -> Optional[Dict]:
    """Create a new job record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("jobs").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_job error: {e}")
        return None


def get_job(job_id: str) -> Optional[Dict]:
    """Fetch a single job by ID."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("jobs").select("*").eq("id", job_id).single().execute()
        return result.data
    except Exception as e:
        print(f"get_job error: {e}")
        return None


def get_jobs(company_id: str, status: str = None) -> List[Dict]:
    """Fetch all jobs for a company with optional status filter."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        query = (
            sb.table("jobs")
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
        )
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return result.data or []
    except Exception as e:
        print(f"get_jobs error: {e}")
        return []


def get_jobs_by_client(client_id: str) -> List[Dict]:
    """Fetch all jobs for a specific client."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("jobs")
            .select("*")
            .eq("client_id", client_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_jobs_by_client error: {e}")
        return []


def update_job(job_id: str, data: dict) -> Optional[Dict]:
    """Update job fields."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("jobs").update(data).eq("id", job_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_job error: {e}")
        return None


# ─── SCHEDULE ────────────────────────────────────────────────────────────────

def create_schedule_entry(data: dict) -> Optional[Dict]:
    """Create a schedule entry."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("schedule").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_schedule_entry error: {e}")
        return None


def get_schedule(company_id: str, date_from: str = None, date_to: str = None) -> List[Dict]:
    """Fetch schedule entries for a company within an optional date range."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        query = (
            sb.table("schedule")
            .select("*, jobs(title, status, trade_type, client_id, address, city), clients(name, phone, email)")
            .eq("company_id", company_id)
            .order("date")
            .order("start_time")
        )
        if date_from:
            query = query.gte("date", date_from)
        if date_to:
            query = query.lte("date", date_to)
        result = query.execute()
        return result.data or []
    except Exception as e:
        print(f"get_schedule error: {e}")
        return []


def get_schedule_by_job(job_id: str) -> List[Dict]:
    """Fetch all schedule entries for a specific job."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("schedule")
            .select("*")
            .eq("job_id", job_id)
            .order("date")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_schedule_by_job error: {e}")
        return []


def update_schedule_entry(schedule_id: str, data: dict) -> Optional[Dict]:
    """Update a schedule entry."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("schedule").update(data).eq("id", schedule_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_schedule_entry error: {e}")
        return None


def delete_schedule_entry(schedule_id: str) -> bool:
    """Delete a schedule entry."""
    try:
        sb = get_supabase()
        if not sb:
            return False
        sb.table("schedule").delete().eq("id", schedule_id).execute()
        return True
    except Exception as e:
        print(f"delete_schedule_entry error: {e}")
        return False


# ─── CREW ────────────────────────────────────────────────────────────────────

def assign_crew(data: dict) -> Optional[Dict]:
    """Assign a crew member to a schedule entry."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("crew_assignments").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"assign_crew error: {e}")
        return None


def get_crew_for_schedule(schedule_id: str) -> List[Dict]:
    """Fetch crew assignments for a schedule entry."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("crew_assignments")
            .select("*, users(name, email, phone, role, avatar_url)")
            .eq("schedule_id", schedule_id)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_crew_for_schedule error: {e}")
        return []


def get_crew_assignments_by_job(job_id: str) -> List[Dict]:
    """Fetch all crew assignments for a job."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("crew_assignments")
            .select("*, users(name, email, phone, role)")
            .eq("job_id", job_id)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_crew_assignments_by_job error: {e}")
        return []


def update_crew_assignment(assignment_id: str, data: dict) -> Optional[Dict]:
    """Update a crew assignment record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("crew_assignments").update(data).eq("id", assignment_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_crew_assignment error: {e}")
        return None


# ─── MEDIA ───────────────────────────────────────────────────────────────────

def create_media_record(data: dict) -> Optional[Dict]:
    """Create a job media record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("job_media").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_media_record error: {e}")
        return None


def get_job_media(job_id: str) -> List[Dict]:
    """Fetch all media for a job."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("job_media")
            .select("*, users(name)")
            .eq("job_id", job_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_job_media error: {e}")
        return []


# ─── PAYMENTS ────────────────────────────────────────────────────────────────

def create_payment(data: dict) -> Optional[Dict]:
    """Create a payment record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("payments").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_payment error: {e}")
        return None


def get_payments_by_job(job_id: str) -> List[Dict]:
    """Fetch all payments for a job."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("payments")
            .select("*")
            .eq("job_id", job_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_payments_by_job error: {e}")
        return []


def get_payments_by_company(company_id: str) -> List[Dict]:
    """Fetch all payments for a company."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("payments")
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_payments_by_company error: {e}")
        return []


def update_payment(payment_id: str, data: dict) -> Optional[Dict]:
    """Update a payment record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("payments").update(data).eq("id", payment_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"update_payment error: {e}")
        return None


# ─── MESSAGES ────────────────────────────────────────────────────────────────

def send_message(data: dict) -> Optional[Dict]:
    """Insert a new message record."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("messages").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"send_message error: {e}")
        return None


def get_conversation(user1_id: str, user2_id: str, job_id: str = None) -> List[Dict]:
    """Fetch messages between two users, optionally filtered by job."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        query = sb.table("messages").select("*").or_(
            f"and(sender_id.eq.{user1_id},recipient_id.eq.{user2_id}),"
            f"and(sender_id.eq.{user2_id},recipient_id.eq.{user1_id})"
        )
        if job_id:
            query = query.eq("job_id", job_id)
        result = query.order("created_at").execute()
        return result.data or []
    except Exception as e:
        print(f"get_conversation error: {e}")
        return []


def get_all_conversations(company_id: str, user_id: str) -> List[Dict]:
    """Get the latest message per conversation thread for a user."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("messages")
            .select("*, sender:sender_id(name, avatar_url), recipient:recipient_id(name, avatar_url)")
            .eq("company_id", company_id)
            .or_(f"sender_id.eq.{user_id},recipient_id.eq.{user_id}")
            .order("created_at", desc=True)
            .execute()
        )
        messages = result.data or []
        # Deduplicate to get one thread per conversation partner
        seen_pairs = set()
        threads = []
        for msg in messages:
            other_id = msg["recipient_id"] if msg["sender_id"] == user_id else msg["sender_id"]
            pair = tuple(sorted([user_id, other_id]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                threads.append(msg)
        return threads
    except Exception as e:
        print(f"get_all_conversations error: {e}")
        return []


def mark_messages_read(recipient_id: str, sender_id: str) -> bool:
    """Mark all messages from sender to recipient as read."""
    try:
        sb = get_supabase()
        if not sb:
            return False
        sb.table("messages").update({"is_read": True}).eq("recipient_id", recipient_id).eq(
            "sender_id", sender_id
        ).eq("is_read", False).execute()
        return True
    except Exception as e:
        print(f"mark_messages_read error: {e}")
        return False


def get_unread_count(user_id: str) -> int:
    """Get the total number of unread messages for a user."""
    try:
        sb = get_supabase()
        if not sb:
            return 0
        result = (
            sb.table("messages")
            .select("id", count="exact")
            .eq("recipient_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        return result.count or 0
    except Exception as e:
        print(f"get_unread_count error: {e}")
        return 0


# ─── EMAIL LOG ───────────────────────────────────────────────────────────────

def log_email(data: dict) -> Optional[Dict]:
    """Log an email send event to the database."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("email_log").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"log_email error: {e}")
        return None


def get_email_log(company_id: str, limit: int = 50) -> List[Dict]:
    """Fetch recent email log entries for a company."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = (
            sb.table("email_log")
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"get_email_log error: {e}")
        return []


# ─── NOTIFICATIONS ───────────────────────────────────────────────────────────

def create_notification(user_id: str, type: str, title: str, content: str) -> Optional[Dict]:
    """Create a notification for a user."""
    try:
        sb = get_supabase()
        if not sb:
            return None
        result = sb.table("notifications").insert(
            {"user_id": user_id, "type": type, "title": title, "content": content}
        ).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"create_notification error: {e}")
        return None


def get_notifications(user_id: str, unread_only: bool = False) -> List[Dict]:
    """Fetch notifications for a user."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        query = (
            sb.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        if unread_only:
            query = query.eq("is_read", False)
        result = query.execute()
        return result.data or []
    except Exception as e:
        print(f"get_notifications error: {e}")
        return []


def mark_notification_read(notification_id: str) -> bool:
    """Mark a single notification as read."""
    try:
        sb = get_supabase()
        if not sb:
            return False
        sb.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return True
    except Exception as e:
        print(f"mark_notification_read error: {e}")
        return False


def get_unread_notifications_count(user_id: str) -> int:
    """Return the count of unread notifications for a user."""
    try:
        sb = get_supabase()
        if not sb:
            return 0
        result = (
            sb.table("notifications")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        return result.count or 0
    except Exception as e:
        print(f"get_unread_notifications_count error: {e}")
        return 0


# ─── DASHBOARD STATS ─────────────────────────────────────────────────────────

def get_dashboard_stats(company_id: str) -> Dict:
    """Aggregate dashboard statistics for a company."""
    stats = {
        "total_clients": 0,
        "active_jobs": 0,
        "open_estimates": 0,
        "total_revenue": 0.0,
        "jobs_this_month": 0,
        "revenue_this_month": 0.0,
        "recent_activity": [],
    }
    try:
        sb = get_supabase()
        if not sb:
            return stats

        # Total clients
        clients_res = (
            sb.table("clients")
            .select("id", count="exact")
            .eq("company_id", company_id)
            .execute()
        )
        stats["total_clients"] = clients_res.count or 0

        # Active jobs
        active_res = (
            sb.table("jobs")
            .select("id", count="exact")
            .eq("company_id", company_id)
            .in_("status", ["scheduled", "in_progress"])
            .execute()
        )
        stats["active_jobs"] = active_res.count or 0

        # Open estimates
        open_est_res = (
            sb.table("estimates")
            .select("id", count="exact")
            .eq("company_id", company_id)
            .in_("status", ["draft", "sent"])
            .execute()
        )
        stats["open_estimates"] = open_est_res.count or 0

        # Total revenue (paid payments)
        payments_res = (
            sb.table("payments")
            .select("amount")
            .eq("company_id", company_id)
            .eq("status", "paid")
            .execute()
        )
        if payments_res.data:
            stats["total_revenue"] = sum(
                float(p.get("amount", 0) or 0) for p in payments_res.data
            )

        # This month stats
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        jobs_month_res = (
            sb.table("jobs")
            .select("id", count="exact")
            .eq("company_id", company_id)
            .gte("created_at", month_start)
            .execute()
        )
        stats["jobs_this_month"] = jobs_month_res.count or 0

        payments_month_res = (
            sb.table("payments")
            .select("amount")
            .eq("company_id", company_id)
            .eq("status", "paid")
            .gte("created_at", month_start)
            .execute()
        )
        if payments_month_res.data:
            stats["revenue_this_month"] = sum(
                float(p.get("amount", 0) or 0) for p in payments_month_res.data
            )

        # Recent activity — last 10 jobs
        recent_jobs_res = (
            sb.table("jobs")
            .select("id, title, status, created_at, trade_type")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        activity = []
        for j in (recent_jobs_res.data or []):
            activity.append(
                {
                    "type": "job",
                    "title": j.get("title", "Untitled Job"),
                    "detail": f"Status: {j.get('status', 'unknown')}",
                    "time": j.get("created_at", ""),
                }
            )

        recent_est_res = (
            sb.table("estimates")
            .select("id, trade_type, status, total, created_at")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        for e in (recent_est_res.data or []):
            activity.append(
                {
                    "type": "estimate",
                    "title": f"{e.get('trade_type', '').title()} Estimate",
                    "detail": f"${float(e.get('total', 0) or 0):,.2f} — {e.get('status', '')}",
                    "time": e.get("created_at", ""),
                }
            )

        # Sort by time descending and take top 10
        activity.sort(key=lambda x: x.get("time", ""), reverse=True)
        stats["recent_activity"] = activity[:10]

    except Exception as e:
        print(f"get_dashboard_stats error: {e}")

    return stats
