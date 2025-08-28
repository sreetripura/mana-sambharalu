from __future__ import annotations
import os, time, typing as t
import requests

# ---------- config ----------
try:
    from config.settings import DEMO_MODE, API_BASE
except Exception:
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes"}
    API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")

TIMEOUT = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p is not None)

JsonLike = t.Union[dict, list, str, None]

class SwechaAPIClient:
    """
    Streamlit-facing client with:
      - DEMO mode (no network): demo login + demo OTP (000000) and token
      - LIVE mode: resilient endpoint fallbacks and payload variants
    """

    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = None
        if os.getenv("SWECHA_TOKEN"):
            self.set_auth_token(os.getenv("SWECHA_TOKEN"))  # pragma: no cover

    # ---------------- low-level HTTP ----------------
    def set_auth_token(self, token: str) -> None:
        self.token = token

    def _headers(self, content_json: bool = True) -> dict:
        h = {"User-Agent": "mana-sambharalu/1.0"}
        if content_json:
            h["Content-Type"] = "application/json"
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: t.Any | None = None,
        params: dict | None = None,
        headers_json: bool = True,
    ) -> t.Tuple[int, JsonLike]:
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
            ct = (r.headers.get("content-type") or "").lower()
            body: JsonLike
            if "application/json" in ct:
                body = r.json()
            else:
                body = r.text
            return r.status_code, body
        except Exception as e:  # pragma: no cover
            return 0, {"error": str(e), "url": url}

    # Helper: try several paths/payloads until one returns 200/201 + dict
    def _post_first_ok(self, paths: t.Iterable[str], payloads: t.Iterable[dict]) -> dict | None:
        for p in paths:
            for pl in payloads:
                sc, body = self._request("POST", p, json_body=pl)
                if sc in (200, 201) and isinstance(body, dict):
                    return body
        return None

    # --------------- auth: login/me -----------------
    def login(self, phone: str, password: str) -> dict | None:
        """
        Password login.
        DEMO_MODE: password must be 'demo123' → returns a demo token.
        LIVE: tries multiple payload names and endpoints.
        """
        if DEMO_MODE:
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token, "user": {"full_name": "Demo User"}}
            return None

        paths = ("auth/login", "login", "auth/signin", "signin", "auth/token")
        payloads = (
            {"phone": phone, "password": password},
            {"phone_number": phone, "password": password},
            {"username": phone, "password": password},
        )
        body = self._post_first_ok(paths, payloads)
        if body and "access_token" in body:
            self.token = body["access_token"]
            return body
        return None

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "me", "users/me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # --------------- signup / OTP -------------------
    def send_signup_otp(self, phone: str) -> dict | None:
        """
        Request an OTP for phone verification.
        DEMO_MODE: pretend to send; hint 000000.
        """
        if DEMO_MODE:
            return {"ok": True, "demo_otp": "000000"}

        paths = ("auth/send-otp", "send-otp", "auth/signup/send-otp")
        payloads = ({"phone": phone}, {"phone_number": phone})
        return self._post_first_ok(paths, payloads)

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
        Verify OTP & create the user. In DEMO, also issues a token so the user is logged in.
        """
        if DEMO_MODE:
            # Accept 000000 and issue a demo token so the UI becomes authenticated
            if otp_code == "000000":
                self.token = "DEMO_TOKEN"
                return {"ok": True, "access_token": self.token, "user": {"full_name": name, "phone": phone}}
            return {"ok": False, "error": "Invalid demo OTP. Use 000000."}

        # Accept both otp/otp_code naming and phone/phone_number
        payload_variants = (
            {"phone": phone, "otp": otp_code, "name": name, "email": email,
             "password": password, "has_given_consent": bool(has_given_consent)},
            {"phone_number": phone, "otp_code": otp_code, "name": name, "email": email,
             "password": password, "has_given_consent": bool(has_given_consent)},
        )
        paths = ("auth/signup/verify", "signup/verify", "auth/verify-otp")
        body = self._post_first_ok(paths, payload_variants)
        if body:
            # Some backends also return a token here; if present, keep it
            tok = body.get("access_token")
            if tok:
                self.token = tok
            return body
        return None

    def resend_signup_otp(self, phone: str) -> dict | None:
        if DEMO_MODE:
            return {"ok": True}
        paths = ("auth/resend-otp", "resend-otp", "auth/signup/resend-otp")
        payloads = ({"phone": phone}, {"phone_number": phone})
        return self._post_first_ok(paths, payloads)

    # --------------- catalog ------------------------
    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        for p in ("categories", "categories/"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, list):
                return body
        return None

    def get_records(self) -> list[dict] | None:
        if DEMO_MODE:
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
        # Some backends wrap as {"items":[...]} or {"results":[...]}
        if sc == 200 and isinstance(body, dict):
            return body.get("items") or body.get("results")
        return None

    def search_records(self, query: str) -> list[dict] | None:
        if DEMO_MODE:
            q = (query or "").lower()
            base = self.get_records() or []
            return [r for r in base if q in r["title"].lower() or q in r["description"].lower()]
        # Prefer explicit search, fallback to filter param on /records
        for p in ("records/search", "records"):
            sc, body = self._request("GET", p, params={"q": query})
            if sc == 200 and isinstance(body, list):
                return body
            if sc == 200 and isinstance(body, dict):
                return body.get("items") or body.get("results")
        return None

    # --------------- contribute / upload ------------
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

        url = _join(self.base, "records/upload/chunk")
        try:
            files = {"file": (filename, chunk, "application/octet-stream")}
            data = {
                "chunk_index": str(chunk_index),
                "total_chunks": str(total_chunks),
                "upload_uuid": upload_uuid,
            }
            r = requests.post(url, headers=self._headers(content_json=False), files=files, data=data, timeout=TIMEOUT)
            if r.status_code in (200, 201):
                if "application/json" in (r.headers.get("content-type") or "").lower():
                    return r.json()
                return {"ok": True}
        except Exception:  # pragma: no cover
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
