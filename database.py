"""Optional Supabase persistence for user-owned tasks and expenses.

When Supabase is not configured, the app continues to work in session-only mode.
Never put the Supabase service-role key in this app; use the publishable/anon key
with the row-level security policies in supabase_schema.sql.
"""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret(name):
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, "").strip()


def is_configured():
    return bool(_secret("SUPABASE_URL") and _secret("SUPABASE_ANON_KEY"))


@st.cache_resource
def _client():
    from supabase import create_client
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("Supabase is not configured.")
    return create_client(url, key)


def get_client():
    """Return the cached Supabase client, or None if persistence is not configured."""
    if not is_configured():
        return None
    return _client()


def sign_up(email, password):
    return get_client().auth.sign_up({"email": email.strip(), "password": password})


def sign_in(email, password):
    response = get_client().auth.sign_in_with_password(
        {"email": email.strip(), "password": password}
    )
    if response.session:
        st.session_state["supabase_access_token"] = response.session.access_token
        st.session_state["supabase_refresh_token"] = response.session.refresh_token
    if response.user:
        st.session_state["supabase_user_id"] = response.user.id
        st.session_state["supabase_user_email"] = response.user.email or email.strip()
    return response


def sign_out():
    try:
        client = get_client()
        token = st.session_state.get("supabase_access_token")
        if client and token:
            client.postgrest.auth(token)
            client.auth.sign_out()
    finally:
        for key in ("supabase_access_token", "supabase_refresh_token",
                    "supabase_user_id", "supabase_user_email"):
            st.session_state.pop(key, None)


def authenticated_client():
    """Create a client scoped to the current user's access token (RLS enforced)."""
    token = st.session_state.get("supabase_access_token")
    if not token:
        return None
    client = get_client()
    if client is not None:
        client.postgrest.auth(token)
    return client


def load_records(table):
    client = authenticated_client()
    if client is None:
        return []
    response = client.table(table).select("*").order("created_at", desc=True).execute()
    return response.data or []


def add_record(table, record):
    client = authenticated_client()
    if client is None:
        raise RuntimeError("Please sign in to save records.")
    response = client.table(table).insert(record).execute()
    return response.data[0] if response.data else None


def update_record(table, record_id, changes):
    client = authenticated_client()
    if client is None:
        raise RuntimeError("Please sign in to save changes.")
    return client.table(table).update(changes).eq("id", record_id).execute()


def delete_record(table, record_id):
    client = authenticated_client()
    if client is None:
        raise RuntimeError("Please sign in to delete records.")
    return client.table(table).delete().eq("id", record_id).execute()
