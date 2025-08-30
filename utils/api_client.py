# utils/api_client.py
from __future__ import annotations
import os, typing as t, requests

try:
    from config.settings import DEMO_MODE, API_BASE
except Exception:
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
    API_BASE  = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")

TIMEOUT = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p is not None)

class SwechaAPIClient:
    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = None

    # ---------------- low-level ----------------
    def set_auth_token(self, token: str) -> None:
        self.token = token

    def _headers(self, *, json_ct: bool = True) -> dict:
        h = {"User-Agent": "mana-sambharalu/1.0"}
        if json_ct:
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
        form_body: dict[str, str] | None = None,
        params: dict | None = None,
        json_ct: bool = True,
    ) -> tuple[int, t.Any]:
        url = _join(self.base, path)
        try:
            if form_body is not None:
                r = requests.request(
                    method, url, headers=self._headers(json_ct=False),
                    data=form_body, params=params, timeout=TIMEOUT,
                )
            else:
                r = requests.request(
                    method, url, headers=self._headers(json_ct=json_ct),
                    json=json_body, params=params, timeout=TIMEOUT,
                )
            ct = r.headers.get("content-type", "")
            body = r.json() if "application/json" in ct else r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    # ---------------- auth ----------------
    def login(self, username_or_phone: str, password: str) -> dict | None:
        """
        Attempt password login against common patterns used by many backends.
        Returns {"access_token": "..."} on success or raises RuntimeError with a helpful message.
        """
        if DEMO_MODE:
            # In live mode you said DEMO_MODE=false, so this block stays unused.
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token}
            return None

        u = username_or_phone

        # Try OAuth2 'password' grant (form-encoded)
        form_candidates = [
            ("POST", "auth/token",  {"username": u, "password": password, "grant_type": "password"}),
            ("POST", "oauth/token", {"username": u, "password": password, "grant_type": "password"}),
            ("POST", "token",       {"username": u, "password": password, "grant_type": "password"}),
            ("POST", "api/token",   {"username": u, "password": password, "grant_type": "password"}),
        ]

        # Try JSON bodies (SimpleJWT / custom)
        json_payloads = [
            {"username": u, "password": password},
            {"email": u,    "password": password},
            {"login": u,    "password": password},
            {"phone": u,    "password": password},
        ]
        json_candidates = [
            ("POST", "auth/jwt/create"),
            ("POST", "auth/token/login"),
            ("POST", "auth/login"),
            ("POST", "users/login"),
            ("POST", "sessions"),
            ("POST", "login"),
        ]

        tried: list[str] = []

        # 1) form endpoints
        for method, path, form in form_candidates:
            sc, body = self._request(method, path, form_body=form)
            tried.append(f"{sc} {path} (form username/password/grant_type)")
            token = self._extract_token(body)
            if sc == 200 and token:
                self.token = token
                return {"access_token": token}

            if sc in (401, 403):
                raise RuntimeError("Invalid credentials.")

        # 2) JSON endpoints
        for method, path in json_candidates:
            for payload in json_payloads:
                sc, body = self._request(method, path, json_body=payload)
                tried.append(f"{sc} {path} ({'/'.join(list(payload.keys()))})")
                token = self._extract_token(body)
                if sc == 200 and token:
                    self.token = token
                    return {"access_token": token}
                if sc in (401, 403):
                    raise RuntimeError("Invalid credentials.")

        # If we’re here, the server likely has no password login endpoint enabled.
        raise RuntimeError(
            "Login endpoint not found on API. "
            "Please ask the API team to enable one of: /auth/token (OAuth), /auth/jwt/create, or /auth/login. "
            + "· Tried: " + " | ".join(tried)
        )

    def _extract_token(self, body: t.Any) -> str | None:
        if not isinstance(body, dict):
            return None
        for k in ("access_token", "token", "jwt"):
            if isinstance(body.get(k), str):
                return body[k]
        # djoser/simplejwt variants
        if "access" in body and isinstance(body["access"], str):
            return body["access"]
        return None

    def read_users_me(self) -> dict | None:
        for p in ("auth/me", "users/me", "me", "profile", "api/me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # ---------------- catalog (unchanged demo fallback) ----------------
    def get_categories(self) -> list[dict] | None:
        sc, body = self._request("GET", "categories")
        if sc == 200 and isinstance(body, list):
            return body
        return [{"id": 1, "name": "Festivals"}]

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
