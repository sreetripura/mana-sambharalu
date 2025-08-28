# utils/api_client.py
from __future__ import annotations
import os, time, json, typing as t
import requests

try:
    # prefer project settings if present
    from config.settings import DEMO_MODE, API_BASE
except Exception:
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes"}
    API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")

TIMEOUT = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p is not None)

class SwechaAPIClient:
    """
    Minimal client used by the Streamlit app.
    - Works in DEMO_MODE without network
    - In live mode talks to Swecha Corpus API (with cautious fallbacks)
    """

    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = None
        # allow token from env (useful in CI)
        tok = os.getenv("SWECHA_TOKEN")
        if tok:
            self.set_auth_token(tok)

    # -------------------------- low-level --------------------------

    def set_auth_token(self, token: str) -> None:
        self.token = token

    def _headers(self, content_json: bool = True) -> dict:
        h = {"User-Agent": "mana-sambharalu/1.0"}
        if content_json:
            h["Content-Type"] = "application/json"
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, path: str, *,
                 json_body: t.Any | None = None,
                 params: dict | None = None,
                 headers_json: bool = True) -> t.Tuple[int, dict | list | str | None]:
        url = _join(self.base, path)
        try:
            r = requests.request(
                method.upper(),
                url,
                headers=self._headers(content_json=headers_json),
                json=json_body,
                params=params,
                timeout=TIMEOUT,
            )
            ct = r.headers.get("content-type", "")
            if "application/json" in ct:
                body = r.json()
            else:
                body = r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    # -------------------------- auth --------------------------

    def login(self, phone: str, password: str) -> dict | None:
        """
        Password login. DEMO_MODE accepts password 'demo123'.
        """
        if DEMO_MODE:
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token, "user": {"full_name": "Demo User"}}
            return None

        payload = {"phone": phone, "password": password}
        # primary path
        sc, body = self._request("POST", "auth/login", json_body=payload)
        if sc == 200 and isinstance(body, dict) and "access_token" in body:
            self.token = body["access_token"]
            return body
        # fallback (older deployments sometimes mount at root)
        sc2, body2 = self._request("POST", "login", json_body=payload)
        if sc2 == 200 and isinstance(body2, dict) and "access_token" in body2:
            self.token = body2["access_token"]
            return body2
        return None

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # --- Sign-Up / OTP (what your friend’s clone is missing) ---

    def send_signup_otp(self, phone: str) -> dict | None:
        """
        Request an OTP to be sent to the given phone.
        """
        if DEMO_MODE:
            # pretend we sent an OTP
            return {"ok": True, "demo_otp": "123456"}

        payload = {"phone": phone}
        for p in ("auth/send-otp", "send-otp", "auth/signup/send-otp"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None

    def verify_signup_otp(
        self,
        *,
        phone: str,
        otp_code: str,
        name: str,
        email: str,
        password: str,
        has_given_consent: bool = True,
    ) -> dict | None:
        """
        Verify OTP and complete registration.
        """
        if DEMO_MODE:
            # accept OTP in demo
            return {"ok": True, "user": {"full_name": name, "phone": phone}}

        payload = {
            "phone": phone,
            "otp": otp_code,
            "name": name,
            "email": email,
            "password": password,
            "has_given_consent": bool(has_given_consent),
        }
        for p in ("auth/signup/verify", "signup/verify", "auth/verify-otp"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None

    def resend_signup_otp(self, phone: str) -> dict | None:
        if DEMO_MODE:
            return {"ok": True}
        payload = {"phone": phone}
        for p in ("auth/resend-otp", "resend-otp", "auth/signup/resend-otp"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None

    # -------------------------- catalog --------------------------

    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        sc, body = self._request("GET", "categories")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    def get_records(self) -> list[dict] | None:
        if DEMO_MODE:
            # tiny demo set
            return [
                {
                    "id": 1,
                    "title": "Bathukamma Procession",
                    "description": "Floral stacks carried during Bathukamma.",
                    "category_id": 1,
                    "language": "telugu",
                    "location": {"latitude": 17.385, "longitude": 78.487},
                    "media": [],
                },
                {
                    "id": 2,
                    "title": "Bonalu Offerings",
                    "description": "Traditional offerings to the Goddess during Bonalu.",
                    "category_id": 1,
                    "language": "telugu",
                    "location": {"latitude": 17.406, "longitude": 78.477},
                    "media": [],
                },
            ]
        sc, body = self._request("GET", "records")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    def search_records(self, query: str) -> list[dict] | None:
        if DEMO_MODE:
            q = (query or "").lower()
            return [r for r in (self.get_records() or []) if q in r["title"].lower() or q in r["description"].lower()]
        for p in ("records/search", "records"):
            sc, body = self._request("GET", p, params={"q": query})
            if sc == 200 and isinstance(body, (list, dict)):
                return body if isinstance(body, list) else body.get("items")
        return None

    # -------------------------- contribute/upload --------------------------

    def create_record(
        self,
        *,
        title: str,
        description: str,
        category_id: int,
        language: str,
        release_rights: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict | None:
        if DEMO_MODE:
            # pretend to create and return an id
            return {"id": int(time.time()) % 100000, "ok": True}

        payload = {
            "title": title,
            "description": description,
            "category_id": category_id,
            "language": language,
            "release_rights": release_rights,
            "location": {"latitude": latitude, "longitude": longitude},
        }
        sc, body = self._request("POST", "records", json_body=payload)
        if sc in (200, 201) and isinstance(body, dict):
            return body
        return None

    def upload_file_chunk(
        self,
        *,
        chunk: bytes,
        filename: str,
        chunk_index: int,
        total_chunks: int,
        upload_uuid: str,
    ) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "uuid": upload_uuid, "idx": chunk_index}

        # chunked endpoint
        url = _join(self.base, "records/upload/chunk")
        try:
            files = {
                "file": (filename, chunk, "application/octet-stream"),
            }
            data = {
                "chunk_index": str(chunk_index),
                "total_chunks": str(total_chunks),
                "upload_uuid": upload_uuid,
            }
            r = requests.post(url, headers=self._headers(content_json=False), files=files, data=data, timeout=TIMEOUT)
            if r.status_code in (200, 201):
                return r.json() if "application/json" in r.headers.get("content-type", "") else {"ok": True}
        except Exception:
            pass
        return None

    def finalize_record_upload(
        self,
        *,
        record_id: int | None = None,
        filename: str,
        total_chunks: int,
        upload_uuid: str,
        media_type: str,
    ) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "record_id": record_id or 0}

        payload = {
            "record_id": record_id,
            "filename": filename,
            "total_chunks": total_chunks,
            "upload_uuid": upload_uuid,
            "media_type": media_type,
        }
        for p in ("records/upload/finalize", "records/upload"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None
