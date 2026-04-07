"""Configuration module for ABA Competitor Analysis Tool."""

import os
from typing import List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
# Try environment variables first (.env file), then fall back to Streamlit secrets (for Cloud)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if GOOGLE_MAPS_API_KEY:
    print(f"[CONFIG] Loaded API key from environment: {GOOGLE_MAPS_API_KEY[:10]}...")
else:
    try:
        import streamlit as st

        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        print(f"[CONFIG] Loaded API key from Streamlit secrets: {GOOGLE_MAPS_API_KEY[:10]}...")
    except (ImportError, AttributeError, KeyError, FileNotFoundError):
        print("[CONFIG] No API key found in environment or Streamlit secrets")

# Search Configuration
DEFAULT_SEARCH_RADIUS_KM = 3
MAX_SEARCH_RADIUS_KM = 10

DEFAULT_SEARCH_KEYWORDS: List[str] = [
    "ABA therapy",
    "applied behavior analysis",
    "autism therapy center",
    "behavioral health clinic",
]

# Service Type Detection Keywords
IN_HOME_KEYWORDS: List[str] = [
    "in-home",
    "in home",
    "mobile",
    "home-based",
    "home based",
    "telehealth",
    "virtual",
    "travel",
    "your home",
]

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "ABA Competitor Analysis Tool | Tuscany Strategy",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
