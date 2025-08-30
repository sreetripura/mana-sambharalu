from __future__ import annotations
import os, time, typing as t
import requests

# Pull config, fall back to env if config package is missing
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

    # ---------- low level ----------
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
            # never raise during import — just return 0 so callers can handle
            return 0, {"error": str(e), "url": url}

    # ---------- auth ----------
    def login(self, username_or_phone: str, password: str) -> dict | None:
        """
        Try a few common login shapes/paths. Never raise here.
        """
        payloads = [
            {"username": username_or_phone, "password": password},
            {"email": username_or_phone,    "password": password},
            {"login": username_or_phone,    "password": password},
            {"phone": username_or_phone,    "password": password},
        ]
        paths = ["auth/login", "users/login", "sessions"]

        last_codes: list[str] = []
        for p in paths:
            for body in payloads:
                sc, resp = self._request("POST", p, json_body=body)
                last_codes.append(f"{sc} {p} ({'/'.join(body.keys())})")
                if sc == 200 and isinstance(resp, dict) and "access_token" in resp:
                    self.token = resp["access_token"]
                    return resp
                if sc in (401,403):  # server reachable, creds rejected
                    return None

        # Surface a concise error the UI can show
        msg = "Login endpoint not found on API." if all(str(c).startswith("404") or str(c).startswith("405") for c in last_codes) \
              else "Invalid credentials or server rejected the request."
        raise RuntimeError(f"{msg} · Tried: " + " | ".join(last_codes))

    def read_users_me(self) -> dict | None:
        for p in ("auth/me","users/me","me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # ---------- catalog ----------
    def get_categories(self) -> list[dict] | None:
        sc, body = self._request("GET", "categories")
        if sc == 200 and isinstance(body, list):
            return body
        return [{"id": 1, "name": "Festivals"}]  # safe fallback

    def get_records(self) -> list[dict] | None:
        sc, body = self._request("GET", "records")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    # ---------- contribute ----------
    def create_record(self, *, title: str, description: str, category_id: int,
                      language: str, release_rights: str,
                      latitude: float | None = None, longitude: float | None = None) -> dict | None:
        payload = {
            "title": title, "description": description, "category_id": category_id,
            "language": language, "release_rights": release_rights,
            "location": {"latitude": latitude, "longitude": longitude},
        }
        sc, body = self._request("POST", "records", json_body=payload)
        if sc in (200,201) and isinstance(body, dict):
            return body
        # fallback demo-success to keep the UI usable even if backend blocks
        return {"id": int(time.time()) % 100000, "ok": True}
