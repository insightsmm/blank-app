import streamlit as st
import bcrypt
from utils.db import get_user_by_email, create_user, get_company, create_company, get_supabase


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))
    except Exception as e:
        print(f"verify_password error: {e}")
        return False


def check_authentication() -> bool:
    """Return True if the current session is authenticated."""
    return bool(st.session_state.get("authenticated", False))


def login_user(user: dict, company: dict) -> None:
    """Populate session state with authenticated user and company data."""
    st.session_state.authenticated = True
    st.session_state.user = user
    st.session_state.company = company
    st.session_state.role = user.get("role", "crew")


def logout_user() -> None:
    """Clear all session state and trigger a page rerun to show the login screen."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def get_current_user() -> dict | None:
    """Return the currently logged-in user dict, or None."""
    return st.session_state.get("user", None)


def get_current_company() -> dict | None:
    """Return the currently logged-in company dict, or None."""
    return st.session_state.get("company", None)


def require_role(*roles) -> bool:
    """
    Check if the current user has one of the specified roles.
    Displays an error and returns False if not authorized.
    """
    current_role = st.session_state.get("role", "")
    if current_role not in roles:
        st.error(
            f"Access denied. This section requires one of the following roles: "
            f"{', '.join(roles)}. Your role: {current_role or 'unknown'}."
        )
        return False
    return True


def is_role(*roles) -> bool:
    """Return True if the current user's role is among the given roles."""
    return st.session_state.get("role", "") in roles
