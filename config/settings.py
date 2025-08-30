import os

# Use LIVE API as you asked
DEMO_MODE = False
API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")
