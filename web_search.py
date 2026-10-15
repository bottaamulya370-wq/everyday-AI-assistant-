import os

import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


def _get_tavily_key():
    """Read the key from Streamlit Secrets, then local environment."""
    try:
        value = st.secrets.get("TAVILY_API_KEY", "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv("TAVILY_API_KEY", "").strip()


def search_web(query, news_mode=False, max_results=8):
    """Return recent web/news results from Tavily."""
    api_key = _get_tavily_key()
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY is missing. Add it in Streamlit Settings > Secrets."
        )

    client = TavilyClient(api_key=api_key)
    options = {
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }
    if news_mode:
        options.update({"topic": "news", "time_range": "day"})
    else:
        options.update({"topic": "general", "time_range": "week"})

    response = client.search(**options)
    return response.get("results", [])
