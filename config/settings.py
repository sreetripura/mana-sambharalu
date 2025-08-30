import os
DEMO_MODE = False
API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")

# Temporarily let Explore open if login is still being wired up.
ALLOW_ANON_EXPLORE = os.getenv("ALLOW_ANON_EXPLORE", "true").lower() in {"1","true","yes"}
