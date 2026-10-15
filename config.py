
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_secret(name, default=""):
    # First, check Streamlit's secure secrets.
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value).strip()
    except Exception:
        # Local development may not have a secrets.toml file.
        pass

    # Then check local environment variables or .env.
    return os.getenv(name, default).strip()

API_KEY = get_secret("GEMINI_API_KEY")
MODEL_NAME = get_secret(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

if not API_KEY:
    raise ValueError(
        "Gemini API key is missing. "
        "Configure GEMINI_API_KEY in .env or Streamlit Secrets."
    )
