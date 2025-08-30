# utils/api_client.py
from __future__ import annotations
import os, requests

# ---- defaults from env; safe even if config.settings is missing
API_BASE = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes", "on")
API_TOKEN = os.getenv("API_TOKEN", "")

# If config/settings.py exists, let it override the above (but don’t crash if it doesn’t).
try:  # optional, safe
    from config.settings import DEMO_MODE as _DM, API_BASE as _AB, API_TOKEN as _AT  # type: ignore
    if _DM is not None:
        DEMO_MODE = _DM
    if _AB:
        API_BASE = str(_AB).rstrip("/")
    if _AT:
        API_TOKEN = str(_AT)
except Exception:
    pass


class SwechaAPIClient:
    def __init__(self, api_base: str | None = None):
        self.api_base = (api_base or API_BASE).rstrip("/")
        self.session = requests.Session()
        self.token: str | None = API_TOKEN or None
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    # --------------- helpers ---------------
    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.api_base}/{path.lstrip('/')}"
        try:
            r = self.session.request(method, url, timeout=20, **kwargs)
            try:
                body = r.json()
            except Exception:
                body = r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e)}

    def set_auth_token(self, token: str) -> None:
        self.token = token
        self.session.headers["Authorization"] = f"Bearer {token}"

    def set_token_and_verify(self, token: str) -> bool:
        self.set_auth_token(token)
        return bool(self.read_users_me())

    # --------------- auth ---------------
    def login(self, username_or_phone: str, password: str) -> dict | None:
        """Password login. In DEMO mode accepts any username with password 'demo123'."""
        if DEMO_MODE:
            if password == "demo123":
                return {"access_token": "demo-token", "user": {"username": username_or_phone}}
            return None

        # Try common endpoints/payloads used by typical backends.
        attempts = [
            # OAuth2-style token endpoints (form)
            ("auth/token", {"username": username_or_phone, "password": password, "grant_type": "password"}, "form"),
            ("oauth/token", {"username": username_or_phone, "password": password, "grant_type": "password"}, "form"),
            ("token", {"username": username_or_phone, "password": password, "grant_type": "password"}, "form"),
            ("api/token", {"username": username_or_phone, "password": password, "grant_type": "password"}, "form"),
            # JWT endpoints (json)
            ("auth/jwt/create", {"username": username_or_phone, "password": password}, "json"),
            ("auth/token/login", {"username": username_or_phone, "password": password}, "json"),
            # Plain login (json)
            ("auth/login", {"username": username_or_phone, "password": password}, "json"),
            ("users/login", {"username": username_or_phone, "password": password}, "json"),
            ("sessions", {"username": username_or_phone, "password": password}, "json"),
            ("login", {"username": username_or_phone, "password": password}, "json"),
        ]

        tried = []
        for path, body, style in attempts:
            kwargs = {"data": body} if style == "form" else {"json": body}
            sc, resp = self._request("POST", path, **kwargs)
            tried.append(f"{sc} {path} ({style} {','.join(body.keys())})")

            if sc == 200 and isinstance(resp, dict):
                token = (
                    resp.get("access_token")
                    or resp.get("token")
                    or resp.get("jwt")
                    or resp.get("key")
                )
                if token:
                    self.set_auth_token(token)
                    return {"access_token": token}

            if sc in (401, 403):
                break  # server exists & rejected creds; stop trying other shapes

        # summarize error
        first_codes = [t.split()[0] for t in tried if t]
        all_missing = first_codes and all(c in ("404", "405") for c in first_codes)
        msg = "Login endpoint not found on API." if all_missing else "Invalid credentials or server rejected the request."
        raise RuntimeError(f"{msg} · Tried: " + " | ".join(tried))

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"full_name": "Demo User"}
        for p in ("auth/me", "users/me", "me", "profile", "api/me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # --------------- signup (demo stubs) ---------------
    def send_signup_otp(self, phone: str) -> dict | None:
        if DEMO_MODE:
            return {"sent": True, "demo_otp": "123456"}
        # If your backend has an endpoint, add it here.
        return None

    def verify_signup_otp(self, *, phone: str, otp_code: str, name: str, email: str, password: str) -> bool:
        if DEMO_MODE:
            return otp_code == "123456"
        # Wire your real endpoint here.
        return False

    # --------------- data ---------------
    def get_categories(self):
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        for p in ("categories", "api/categories", "records/categories"):
            sc, body = self._request("GET", p)
            if sc == 200:
                return body
        return []

    def create_record(self, **payload):
        if DEMO_MODE:
            # pretend success
            return {"id": 1, "demo": True, **payload}
        for p in ("records", "api/records", "items"):
            sc, body = self._request("POST", p, json=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None
