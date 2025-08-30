import os
DEMO_MODE = False
API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")
# Keep Explore/Contribute gated (set to True only if you want to preview without login)
ALLOW_ANON_EXPLORE = False
