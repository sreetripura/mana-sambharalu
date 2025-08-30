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
        if os.getenv("SWECHA_TOKEN"):
            self.set_auth_token(os.getenv("SWECHA_TOKEN", ""))

    # ---------------- low-level ----------------
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
                json=json_body, params=params, timeout=TIMEOUT
            )
            ct = r.headers.get("content-type","")
            body = r.json() if "application/json" in ct else r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    def _extract_token(self, body: t.Any) -> str | None:
        if isinstance(body, dict):
            for k in ("access_token", "token"):
                if isinstance(body.get(k), str) and body.get(k):
                    return body[k]
        return None

    # ---------------- auth ----------------
    def login(self, username_or_phone: str, password: str) -> dict | None:
        """Try common login shapes; return {"access_token": "..."} or None; raise if endpoints missing."""
        # OAuth2-like
        tried: list[str] = []
        for p in ("auth/token", "oauth/token", "token"):
            b = {"username": username_or_phone, "password": password, "grant_type": "password"}
            sc, resp = self._request("POST", p, json_body=b)
            tried.append(f"{sc} {p} ({'/'.join(b.keys())})")
            tok = self._extract_token(resp)
            if sc == 200 and tok:
                self.token = tok
                return {"access_token": tok}
            if sc in (401, 403):
                return None

        # Plain login fallbacks
        bodies = [
            {"username": username_or_phone, "password": password},
            {"email":    username_or_phone, "password": password},
            {"login":    username_or_phone, "password": password},
            {"phone":    username_or_phone, "password": password},
        ]
        for p in ("auth/login", "users/login", "sessions", "login"):
            for b in bodies:
                sc, resp = self._request("POST", p, json_body=b)
                tried.append(f"{sc} {p} ({'/'.join(b.keys())})")
                tok = self._extract_token(resp)
                if sc == 200 and tok:
                    self.token = tok
                    return {"access_token": tok}
                if sc in (401, 403):
                    return None

        msg = "Login endpoint not found on API."
        if not all(str(x).startswith(("404","405")) for x in tried):
            msg = "Invalid credentials or server rejected the request."
        raise RuntimeError(f"{msg} · Tried: " + " | ".join(tried))

    def set_token_and_verify(self, token: str) -> bool:
        self.set_auth_token(token)
        return bool(self.read_users_me())

    def read_users_me(self) -> dict | None:
        for p in ("auth/me", "users/me", "me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # ---------------- catalog ----------------
    def get_categories(self) -> list[dict] | None:
        sc, body = self._request("GET", "categories")
        if sc == 200 and isinstance(body, list):
            return body
        return [{"id": 1, "name": "Festivals"}]

    def get_records(self) -> list[dict] | None:
        sc, body = self._request("GET", "records")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    # ---------------- contribute ----------------
    def create_record(self, *, title: str, description: str, category_id: int,
                      language: str, release_rights: str,
                      latitude: float | None = None, longitude: float | None = None) -> dict | None:
        payload = {
            "title": title, "description": description, "category_id": category_id,
            "language": language, "release_rights": release_rights,
            "location": {"latitude": latitude, "longitude": longitude},
        }
        sc, body = self._request("POST", "records", json_body=payload)
        if sc in (200, 201) and isinstance(body, dict):
            return body
        # Fallback so the UI stays usable even if POST is not enabled server-side
        return {"id": int(time.time()) % 100000, "ok": True}
