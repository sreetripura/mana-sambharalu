# utils/api_client.py
from __future__ import annotations
import os, time, typing as t
import requests

# Project settings
try:
    from config.settings import DEMO_MODE, API_BASE
except Exception:
    DEMO_MODE = False
    API_BASE = os.getenv("API_BASE", "https://api.corpus.swecha.org/api/v1").rstrip("/")

TIMEOUT = 25


def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p is not None)


class SwechaAPIClient:
    """
    Minimal HTTP client for the Corpus API with careful fallbacks.
    Supports: login, /me, categories, create_record, search/list records.
    """

    def __init__(self) -> None:
        self.base = API_BASE
        self.token: t.Optional[str] = None
        tok = os.getenv("SWECHA_TOKEN")
        if tok:
            self.set_auth_token(tok)

    # ------------------------ basics ------------------------

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
    ) -> tuple[int, dict | list | str | None]:
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

    # ------------------------ auth ------------------------

    def login(self, username_or_phone: str, password: str) -> dict | None:
        """
        Password login (phone/email/username + password).
        Returns {"access_token": "..."} on success, else raises RuntimeError with a helpful message.
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
                tried.append(f"{sc} {path} ({'/'.join(list(body.keys()))})")
                if sc == 200 and isinstance(resp, dict) and "access_token" in resp:
                    self.token = resp["access_token"]
                    return resp
                if sc in (401, 403):
                    raise RuntimeError("Invalid credentials or server rejected the request.")

        raise RuntimeError("Login endpoint not found on API. · Tried: " + " | ".join(tried))

    def read_users_me(self) -> dict | None:
        if DEMO_MODE:
            return {"id": 1, "full_name": "Demo User", "phone": "9999999999"}
        for p in ("auth/me", "users/me", "me"):
            sc, body = self._request("GET", p)
            if sc == 200 and isinstance(body, dict):
                return body
        return None

    # ------------------------ categories ------------------------

    def get_categories(self) -> list[dict] | None:
        if DEMO_MODE:
            return [{"id": 1, "name": "Festivals"}]
        sc, body = self._request("GET", "categories")
        if sc == 200 and isinstance(body, list):
            return body
        return None

    # ------------------------ create record ------------------------

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

    # ------------------------ records / search ------------------------

    def get_records(self, **params) -> list[dict] | None:
        if DEMO_MODE:
            return [
                {
                    "id": 1,
                    "title": "బతుకమ్మ",
                    "description": "తెలంగాణ రాష్ట్రంలోని ప్రముఖ పుష్పోత్సవం.",
                    "language": "te",
                    "tags": ["Telangana", "festival"],
                    "media": [],
                },
                {
                    "id": 2,
                    "title": "బోనాలు",
                    "description": "మహాంకాళి అమ్మవారికి బోనాల సమర్పణ.",
                    "language": "te",
                    "tags": ["Telangana", "festival"],
                    "media": [],
                },
            ]

        sc, body = self._request("GET", "records", params=params or None)
        if sc == 200 and isinstance(body, list):
            return body

        if "q" in params:
            sc2, body2 = self._request("GET", "records/search", params=params)
            if sc2 == 200 and isinstance(body2, (list, dict)):
                return body2 if isinstance(body2, list) else body2.get("items")
        return None

    def search_records(self, query: str, **extra) -> list[dict] | None:
        extra = extra or {}
        extra["q"] = query
        return self.get_records(**extra)

    # Convenience used by Explore page
    def fetch_telugu_telangana(self) -> list[dict]:
        items = self.search_records("తెలంగాణ", language="te") or []
        if not items:
            items = self.search_records("Telangana", language="te") or []
        if not items:
            items = [
                {
                    "id": 1001,
                    "title": "బతుకమ్మ",
                    "description": "దసరా ముందు తొమ్మిది రోజులు జరుపుకునే తెలంగాణ పుష్పాల పండుగ.",
                    "language": "te",
                    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Bathukamma_festival_Telangana.jpg/640px-Bathukamma_festival_Telangana.jpg",
                },
                {
                    "id": 1002,
                    "title": "బోనాలు",
                    "description": "ఆశాడ మాసంలో మహాంకాళి అమ్మవారికి నైవేద్యం సమర్పించే ఉత్సవం.",
                    "language": "te",
                    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Bonalu_Telangana.jpg/640px-Bonalu_Telangana.jpg",
                },
                {
                    "id": 1003,
                    "title": "సమ్మక్క-సరలమ్మ జాతర",
                    "description": "ములుగు జిల్లా మేడారం లో జరిగే ఆసియా లోని అతిపెద్ద గిరిజన దేవాలయ జాతర.",
                    "language": "te",
                    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Medaram_Sammakka_Saralamma_Jathara.jpg/640px-Medaram_Sammakka_Saralamma_Jathara.jpg",
                },
                {
                    "id": 1004,
                    "title": "మోహర్రం (పీర్ల పండుగ)",
                    "description": "తెలంగాణలో ప్రత్యేకంగా నిర్వహించే పీర్ల ఊరేగింపులు, సౌభ్రాతృత్వ దైవీ పండుగ.",
                    "language": "te",
                    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Muharram_Telangana.jpg/640px-Muharram_Telangana.jpg",
                },
            ]
        return items
