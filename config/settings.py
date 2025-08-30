import os

# Streamlit Cloud / local: "true" enables DEMO mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").strip().lower() == "true"

# Used only when DEMO_MODE is false
API_BASE  = os.getenv("API_BASE", "").rstrip("/")
API_TOKEN = os.getenv("API_TOKEN", "")
