from __future__ import annotations
import os, time, typing as t
import requests

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1","true","yes"}
API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")
TIMEOUT   = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p)

class SwechaAPIClient:
    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = os.getenv("SWECHA_TOKEN") or None

    def set_auth_token(self, token: str) -> None:
        self.token = token

    def _headers(self, content_json: bool = True) -> dict:
        h = {"User-Agent": "mana-sambharalu/1.0"}
        if content_json:
            h["Content-Type"] = "application/json"
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, path: str, *, json_body=None, params=None, headers_json=True):
        url = _join(self.base, path)
        try:
            r = requests.request(method.upper(), url,
                                 headers=self._headers(content_json=headers_json),
                                 json=json_body, params=params, timeout=TIMEOUT)
            ct = r.headers.get("content-type","")
            body = r.json() if "application/json" in ct else r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    # -------- auth --------
    def login(self, identifier: str, password: str) -> dict | None:
        if DEMO_MODE:
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token, "user": {"full_name": "Demo User"}}
            return {"_error": "DEMO_MODE: wrong password (use demo123)"}

        idv = (identifier or "").strip()
        bases: list[dict] = []
        if idv.startswith("+") or idv.isdigit():
            bases.append({"phone": idv})
        else:
            bases.append({"username": idv})
        bases += [{"email": idv}, {"login": idv}]

        paths = ["auth/login", "login", "auth/sessions", "sessions"]
        tried, first_reject = [], None

        for path in paths:
            for base in bases:
                payload = dict(base); payload["password"] = password
                sc, body = self._request("POST", path, json_body=payload)
                tried.append(f"{sc} {path} ({list(base.keys())[0]}+password)")
                if sc in (200, 201) and isinstance(body, dict):
                    token = (body.get("access_token") or body.get("token") or body.get("access") or
                             (isinstance(body.get("data"), dict) and body["data"].get("access_token")))
                    if token:
                        self.token = token
                        return body
                elif sc in (400,401,403,422) and first_reject is None:
                    # remember the first meaningful rejection so UI can show it
                    first_reject = {"status": sc, "path": path, "payload_keys": list(base.keys()), "body": body}
        if first_reject:
            return {"_error": "rejected", "_details": first_reject, "_tried": tried}
        return {"_error": "not_found", "_tried": tried}

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "me", "users/me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # -------- catalog --------
    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        sc, body = self._request("GET", "categories")
        return body if sc == 200 and isinstance(body, list) else None

    def get_records(self) -> list[dict] | None:
        if DEMO_MODE:
            return [
                {"id": 1, "title": "Bathukamma Procession", "description": "Floral stacks carried during Bathukamma.",
                 "category_id": 1, "language": "telugu", "location": {"latitude": 17.385, "longitude": 78.487}, "media": []},
                {"id": 2, "title": "Bonalu Offerings", "description": "Traditional offerings to the Goddess during Bonalu.",
                 "category_id": 1, "language": "telugu", "location": {"latitude": 17.406, "longitude": 78.477}, "media": []},
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
