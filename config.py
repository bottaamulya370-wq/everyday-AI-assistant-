import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(name, default=""):
    """Read Streamlit Secrets first, then local environment variables."""
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


API_KEY = get_secret("GEMINI_API_KEY")
MODEL_NAME = get_secret("GEMINI_MODEL", "gemini-2.5-flash")
