import os
DEMO_MODE = os.getenv("DEMO_MODE", "true").strip().lower() == "true"
API_BASE  = os.getenv("API_BASE", "").rstrip("/")
API_TOKEN = os.getenv("API_TOKEN", "")
