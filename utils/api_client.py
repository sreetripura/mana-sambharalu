from __future__ import annotations
import os, time, typing as t
import requests

try:
    from config.settings import DEMO_MODE, API_BASE
except Exception:
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1","true","yes"}
    API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")

TIMEOUT = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p is not None)

class SwechaAPIClient:
    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = None
        tok = os.getenv("SWECHA_TOKEN")
        if tok:
            self.set_auth_token(tok)

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
                 headers_json: bool = True) -> tuple[int, dict | list | str | None]:
        url = _join(self.base, path)
        try:
            r = requests.request(
                method.upper(), url,
                headers=self._headers(content_json=headers_json),
                json=json_body, params=params, timeout=TIMEOUT,
            )
            ct = r.headers.get("content-type", "")
            body: dict | list | str | None
            if "application/json" in ct:
                body = r.json()
            else:
                body = r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    # ------------- auth -------------
    def login(self, username_or_phone: str, password: str) -> dict | None:
        """
        Password login (phone/email/username + password).
        Returns {"access_token": "..."} on success, else raises RuntimeError on 404 cascade.
        """
        if DEMO_MODE:
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token, "user": {"full_name": "Demo User"}}
            return None

        payloads = [
            {"username": username_or_phone, "password": password},
            {"email": username_or_phone, "password": password},
            {"login": username_or_phone, "password": password},
            {"phone": username_or_phone, "password": password},
        ]
        candidate_paths = ["auth/login", "users/login", "sessions"]

        tried: list[str] = []
        for path in candidate_paths:
            for body in payloads:
                sc, resp = self._request("POST", path, json_body=body)
                tried.append(f"{sc} {path} ({'/'.join(body.keys())})")
                if sc == 200 and isinstance(resp, dict) and "access_token" in resp:
                    self.token = resp["access_token"]
                    return resp
            # if server exists but rejects creds, stop early
            if any(t.startswith("401 ") or t.startswith("403 ") for t in tried[-len(payloads):]):
                break

        msg = "Login endpoint not found on API." if all(t.startswith("404 ") for t in tried) \
              else "Invalid credentials or server rejected the request."
        raise RuntimeError(f"{msg} · Tried: " + " | ".join(tried))

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "users/me", "me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # --------- sign-up / OTP ----------
    def send_signup_otp(self, phone: str) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "demo_otp": "123456"}
        payload = {"phone": phone}
        for p in ("auth/send-otp", "send-otp", "auth/signup/send-otp"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None

    def verify_signup_otp(
        self, *, phone: str, otp_code: str, name: str, email: str, password: str, has_given_consent: bool = True,
    ) -> dict | None:
        if DEMO_MODE:
            return {"ok": True, "user": {"full_name": name, "phone": phone}}
        payload = {
            "phone": phone, "otp": otp_code, "name": name, "email": email,
            "password": password, "has_given_consent": bool(has_given_consent),
        }
        for p in ("auth/signup/verify", "signup/verify", "auth/verify-otp"):
            sc, body = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(body, dict):
                return body
        return None

    # ------------- catalog -------------
    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        sc, body = self._request("GET", "categories")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    def get_records(self) -> list[dict] | None:
        if DEMO_MODE:
            return []  # Explore will fill with FALLBACK
        sc, body = self._request("GET", "records")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    def search_records(self, query: str) -> list[dict] | None:
        if DEMO_MODE:
            return []  # Explore will fill with FALLBACK
        for p in ("records/search", "records"):
            sc, body = self._request("GET", p, params={"q": query})
            if sc == 200 and isinstance(body, (list, dict)):
                return body if isinstance(body, list) else body.get("items")
        return None

    # ------------- contribute -------------
    def create_record(
        self, *, title: str, description: str, category_id: int, language: str,
        release_rights: str, latitude: float | None = None, longitude: float | None = None,
    ) -> dict | None:
        if DEMO_MODE:
            return {"id":  int(time.time()) % 100000, "ok": True}
        payload = {
            "title": title, "description": description, "category_id": category_id,
            "language": language, "release_rights": release_rights,
            "location": {"latitude": latitude, "longitude": longitude},
        }
        sc, body = self._request("POST", "records", json_body=payload)
        if sc in (200, 201) and isinstance(body, dict):
            return body
        return None
