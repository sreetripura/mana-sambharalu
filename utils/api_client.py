from __future__ import annotations
import os, time, json, typing as t
import requests

# ---- config ----
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1","true","yes"}
API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")
TIMEOUT   = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p)

class SwechaAPIClient:
    """
    Minimal client used by the Streamlit app.
    - DEMO_MODE accepts password 'demo123'
    - Live mode talks to api.corpus.swecha.org with multiple compatible paths
    """
    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = os.getenv("SWECHA_TOKEN") or None

    # ------------- low-level -------------
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
                method.upper(), url,
                headers=self._headers(content_json=headers_json),
                json=json_body, params=params, timeout=TIMEOUT,
            )
            ct = r.headers.get("content-type", "")
            body = r.json() if "application/json" in ct else r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    # ------------- auth -------------
    def login(self, identifier: str, password: str) -> dict | None:
        """
        Try common Swecha/DRF-style auth endpoints in this order:
        1) POST /auth/login
        2) POST /login
        3) POST /auth/sessions
        4) POST /sessions
        With multiple possible identifier keys (phone/username/email/login).
        """
        if DEMO_MODE:
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token, "user": {"full_name": "Demo User"}}
            return None

        idv = (identifier or "").strip()
        bases: list[dict] = []
        if idv.startswith("+") or idv.isdigit():
            bases.append({"phone": idv})
        else:
            bases.append({"username": idv})
        bases += [{"email": idv}, {"login": idv}]

        paths = ["auth/login", "login", "auth/sessions", "sessions"]
        tried: list[str] = []

        for path in paths:
            for base in bases:
                payload = dict(base)
                payload["password"] = password
                sc, body = self._request("POST", path, json_body=payload)
                tried.append(f"{sc} {path} ({list(base.keys())[0]}+password)")
                if sc in (200, 201) and isinstance(body, dict):
                    token = (
                        body.get("access_token")
                        or body.get("token")
                        or body.get("access")
                        or (isinstance(body.get("data"), dict) and body["data"].get("access_token"))
                    )
                    if token:
                        self.token = token
                        return body
        # Surface a crisp error to the UI
        return {"_error": "Login endpoint not found on API. · Tried: " + " | ".join(tried[:6]) + (" ..." if len(tried) > 6 else "")}

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "me", "users/me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # ------------- catalog -------------
    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        sc, body = self._request("GET", "categories")
        return body if sc == 200 and isinstance(body, list) else None

    def get_records(self) -> list[dict] | None:
        if DEMO_MODE:
            return [
                {
                    "id": 1, "title": "Bathukamma Procession",
                    "description": "Floral stacks carried during Bathukamma.",
                    "category_id": 1, "language": "telugu",
                    "location": {"latitude": 17.385, "longitude": 78.487}, "media": []
                },
                {
                    "id": 2, "title": "Bonalu Offerings",
                    "description": "Traditional offerings to the Goddess during Bonalu.",
                    "category_id": 1, "language": "telugu",
                    "location": {"latitude": 17.406, "longitude": 78.477}, "media": []
                },
            ]
        sc, body = self._request("GET", "records")
        return body if sc == 200 and isinstance(body, list) else None

    def search_records(self, query: str) -> list[dict] | None:
        if DEMO_MODE:
            q = (query or "").lower()
            return [r for r in (self.get_records() or []) if q in r["title"].lower() or q in r["description"].lower()]
        for p in ("records/search", "records"):
            sc, body = self._request("GET", p, params={"q": query})
            if sc == 200 and isinstance(body, (list, dict)):
                return body if isinstance(body, list) else body.get("items")
        return None

    # ------------- sign-up / otp -------------
    def send_signup_otp(self, phone: str) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "demo_otp": "123456"}
        payload = {"phone": phone}
        for p in ("auth/send-otp", "send-otp", "auth/signup/send-otp"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None

    def verify_signup_otp(self, *, phone: str, otp_code: str, name: str, email: str, password: str, has_given_consent: bool = True) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "user": {"full_name": name, "phone": phone}}
        payload = {
            "phone": phone, "otp": otp_code, "name": name,
            "email": email, "password": password,
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

    # ------------- contribute/upload -------------
    def create_record(self, *, title: str, description: str, category_id: int, language: str, release_rights: str,
                      latitude: float | None = None, longitude: float | None = None) -> dict | None:
        if DEMO_MODE:
            return {"id": int(time.time()) % 100000, "ok": True}
        payload = {
            "title": title, "description": description, "category_id": category_id,
            "language": language, "release_rights": release_rights,
            "location": {"latitude": latitude, "longitude": longitude},
        }
        sc, body = self._request("POST", "records", json_body=payload)
        return body if sc in (200, 201) and isinstance(body, dict) else None

    def upload_file_chunk(self, *, chunk: bytes, filename: str, chunk_index: int, total_chunks: int, upload_uuid: str) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "uuid": upload_uuid, "idx": chunk_index}
        url = _join(self.base, "records/upload/chunk")
        try:
            files = {"file": (filename, chunk, "application/octet-stream")}
            data = {"chunk_index": str(chunk_index), "total_chunks": str(total_chunks), "upload_uuid": upload_uuid}
            r = requests.post(url, headers=self._headers(content_json=False), files=files, data=data, timeout=TIMEOUT)
            if r.status_code in (200, 201):
                return r.json() if "application/json" in r.headers.get("content-type", "") else {"ok": True}
        except Exception:
            pass
        return None

    def finalize_record_upload(self, *, record_id: int | None = None, filename: str, total_chunks: int, upload_uuid: str, media_type: str) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "record_id": record_id or 0}
        payload = {"record_id": record_id, "filename": filename, "total_chunks": total_chunks, "upload_uuid": upload_uuid, "media_type": media_type}
        for p in ("records/upload/finalize", "records/upload"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None
