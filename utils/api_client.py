from __future__ import annotations
import os, typing as t, requests

# ----- settings -----
API_BASE = os.getenv("API_BASE", "https://api.corpus.swecha.org").rstrip("/")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
TIMEOUT = 25

def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p is not None)

class SwechaAPIClient:
    """
    Minimal client used by the Streamlit app.

    - DEMO_MODE: fake login with password 'demo123'
    - LIVE:     prefers token-paste or OTP login if backend supports it
    """

    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = None
        tok = os.getenv("SWECHA_TOKEN")
        if tok:
            self.set_auth_token(tok)

    # -------- low-level --------
    def set_auth_token(self, token: str) -> None:
        self.token = token

    def _headers(self, *, json_ct: bool = True) -> dict:
        h = {"User-Agent": "mana-sambharalu/1.0"}
        if json_ct:
            h["Content-Type"] = "application/json"
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, path: str, *,
                 json_body: t.Any | None = None,
                 form_body: dict | None = None,
                 params: dict | None = None,
                 json_ct: bool = True) -> tuple[int, t.Any]:
        url = _join(self.base, path)
        try:
            if form_body is not None:
                headers = self._headers(json_ct=False)
                r = requests.request(method.upper(), url,
                                     headers=headers, data=form_body, params=params, timeout=TIMEOUT)
            else:
                headers = self._headers(json_ct=json_ct)
                r = requests.request(method.upper(), url,
                                     headers=headers, json=json_body, params=params, timeout=TIMEOUT)
            ct = r.headers.get("content-type", "")
            body = r.json() if "application/json" in ct else r.text
            return r.status_code, body
        except Exception as e:
            return 0, {"error": str(e), "url": url}

    # -------- auth flows --------
    def login(self, username_or_phone: str, password: str) -> dict | None:
        """
        Primary login. In DEMO_MODE accepts password 'demo123'.
        On LIVE, tries common token-creation endpoints; if none work, raises.
        """
        if DEMO_MODE:
            if password == "demo123":
                self.token = "DEMO_TOKEN"
                return {"access_token": self.token}
            return None

        # 1) OAuth2 password-style (many backends)
        form_payload = {"username": username_or_phone, "password": password, "grant_type": "password"}
        token_paths = ["auth/token", "oauth/token", "token", "api/token", "auth/token/"]
        tried: list[str] = []
        for p in token_paths:
            for as_form in (True, False):
                if as_form:
                    sc, resp = self._request("POST", p, form_body=form_payload)
                    tried.append(f"{sc} {p} (form username/password/grant_type)")
                else:
                    sc, resp = self._request("POST", p, json_body=form_payload)
                    tried.append(f"{sc} {p} (username/password/grant_type)")
                if sc == 200 and isinstance(resp, dict) and "access_token" in resp:
                    self.token = resp["access_token"]; return resp
                if sc in (401, 403):  # creds rejected; stop early
                    raise RuntimeError("Invalid credentials.")

        # 2) JWT / token login variants
        jwt_paths = ["auth/jwt/create", "auth/token/login", "auth/login",
                     "users/login", "sessions", "login"]
        json_payloads = [
            {"username": username_or_phone, "password": password},
            {"email": username_or_phone, "password": password},
            {"login": username_or_phone, "password": password},
            {"phone": username_or_phone, "password": password},
        ]
        for p in jwt_paths:
            for body in json_payloads:
                for as_form in (False, True):
                    if as_form:
                        sc, resp = self._request("POST", p, form_body=body)
                        tried.append(f"{sc} {p} (form {'/'.join(body.keys())})")
                    else:
                        sc, resp = self._request("POST", p, json_body=body)
                        tried.append(f"{sc} {p} ({'/'.join(body.keys())})")
                    if sc == 200 and isinstance(resp, dict) and "access_token" in resp:
                        self.token = resp["access_token"]; return resp
                    if sc in (401, 403):
                        raise RuntimeError("Invalid credentials.")

        # If we get here: backend doesn’t expose password login
        raise RuntimeError("Login endpoint not found on API. · Tried: " + " | ".join(tried))

    def set_token_and_verify(self, token: str) -> bool:
        self.set_auth_token(token)
        me = self.read_users_me()
        return bool(me)

    def send_login_otp(self, phone: str) -> dict | None:
        """Try common OTP-login send endpoints."""
        paths = ["auth/otp/send", "auth/send-otp", "otp/send", "users/otp/send"]
        payload = {"phone": phone}
        for p in paths:
            sc, resp = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(resp, dict):
                return resp
        return None

    def verify_login_otp(self, phone: str, code: str) -> dict | None:
        """Verify OTP for login; expect access_token on success."""
        paths = ["auth/otp/verify", "auth/verify-otp", "otp/verify", "users/otp/verify"]
        payload = {"phone": phone, "otp": code}
        for p in paths:
            sc, resp = self._request("POST", p, json_body=payload)
            if sc in (200, 201) and isinstance(resp, dict) and "access_token" in resp:
                self.token = resp["access_token"]
                return resp
        return None

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "users/me", "me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # -------- catalog (read) --------
    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        sc, body = self._request("GET", "categories")
        return body if sc == 200 and isinstance(body, list) else None

    def get_records(self) -> list[dict] | None:
        if DEMO_MODE:
            return []
        sc, body = self._request("GET", "records")
        return body if sc == 200 and isinstance(body, list) else None

    # -------- contribute (metadata only on this UI) --------
    def create_record(self, *, title: str, description: str, category_id: int,
                      language: str, release_rights: str,
                      latitude: float | None = None, longitude: float | None = None) -> dict | None:
        if DEMO_MODE:
            return {"id": 12345, "ok": True}
        payload = {
            "title": title, "description": description, "category_id": category_id,
            "language": language, "release_rights": release_rights,
            "location": {"latitude": latitude, "longitude": longitude},
        }
        sc, body = self._request("POST", "records", json_body=payload)
        return body if sc in (200, 201) and isinstance(body, dict) else None
