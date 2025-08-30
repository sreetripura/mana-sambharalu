from __future__ import annotations
import os, json, requests
from typing import Any, Dict, Tuple

# --- configuration from env/streamlit secrets ---
API_BASE = os.environ.get("API_BASE") or "https://api.corpus.swecha.org"
DEMO_MODE = bool(int(os.environ.get("DEMO_MODE", "0")))

def _headers(token: str | None) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    return h

class SwechaAPIClient:
    def __init__(self) -> None:
        self.base = API_BASE.rstrip("/")
        self.token: str | None = None

    def set_auth_token(self, token: str | None) -> None:
        self.token = token

    # ------------- low level -------------
    def _request(self, method: str, path: str, *, json_body: Dict | None = None) -> Tuple[int, Any]:
        url = f"{self.base}/{path.lstrip('/')}"
        try:
            r = requests.request(method, url, json=json_body, headers=_headers(self.token), timeout=20)
            try:
                data = r.json()
            except Exception:
                data = r.text
            return r.status_code, data
        except requests.RequestException as e:
            return 0, {"error": str(e)}

    # ------------- auth -------------
    def login(self, username_or_phone: str, password: str) -> Dict | None:
        payloads = [
            {"username": username_or_phone, "password": password},
            {"email": username_or_phone,    "password": password},
            {"login": username_or_phone,    "password": password},
            {"phone": username_or_phone,    "password": password},
        ]
        paths = ["auth/login", "users/login", "sessions"]
        tried = []
        for p in paths:
            for body in payloads:
                sc, resp = self._request("POST", p, json_body=body)
                tried.append(f"{sc} {p} ({'/'.join(body.keys())})")
                if sc in (200, 201) and isinstance(resp, dict) and "access_token" in resp:
                    self.token = resp["access_token"]
                    return resp
                if sc in (401, 403):  # endpoint exists but creds wrong
                    raise RuntimeError("Invalid credentials or server rejected the request.")
        raise RuntimeError("Login endpoint not found on API. · Tried: " + " | ".join(tried))

    def read_users_me(self) -> Dict | None:
        for p in ("auth/me", "users/me", "me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict): return body
        return None

    def send_signup_otp(self, phone: str) -> Dict | None:
        for p in ("auth/send-otp", "auth/otp", "otp/send"):
            sc, body = self._request("POST", p, json_body={"phone": phone})
            if sc in (200, 201) and isinstance(body, dict): return body
        return None

    def verify_signup_otp(self, *, phone: str, otp_code: str, name: str, email: str, password: str) -> bool:
        payload = {"phone": phone, "otp": otp_code, "name": name, "email": email, "password": password}
        for p in ("auth/verify-otp", "auth/register", "users"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201): return True
        return False

    # ------------- catalog -------------
    def get_categories(self) -> list[dict] | None:
        for p in ("categories", "taxonomy/categories"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, list): return body
        return None

    # ------------- create record -------------
    def create_record(
        self, *, title: str, description: str, category_id: int | None, language: str,
        release_rights: str | None, latitude: float | None, longitude: float | None,
        return_debug: bool = False,
    ) -> Tuple[Dict | None, str | None] | Dict | None:
        payload = {
            "title": title,
            "description": description,
            "language": language,
        }
        if category_id: payload["category_id"] = category_id
        if release_rights: payload["license"] = release_rights
        if latitude is not None and longitude is not None:
            payload["location"] = {"lat": latitude, "lon": longitude}

        tried = []
        for p in ("records", "items", "entries", "submissions", "festivals"):
            sc, body = self._request("POST", p, json_body=payload)
            tried.append(f"{sc} {p}")
            if sc in (200, 201) and isinstance(body, dict):  # success
                return (body, None) if return_debug else body
            if sc in (400, 401, 403):  # tell the caller why
                msg = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
                raise RuntimeError(f"Server rejected the request · HTTP {sc}: {msg}")

        # no endpoint worked
        msg = " | ".join(tried)
        if return_debug: return None, ("Create endpoint not found. Tried: " + msg)
        return None
