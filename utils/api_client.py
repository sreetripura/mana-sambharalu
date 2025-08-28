# utils/api_client.py
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple
import requests

# ---------- MODE & SETTINGS ----------
DEMO_MODE: bool = True                           # True = demo data; False = real API
API_BASE: str = "https://api.corpus.swecha.org"  # set your deployment if different
REQ_TIMEOUT: int = 25
RETRY_BACKOFF: float = 0.7
MAX_RETRIES: int = 1
# -------------------------------------

class SwechaAPIClient:
    """Thin client for Swecha Corpus API with demo fallback."""

    # Demo seed so Explore works immediately
    _demo_categories: List[Dict[str, Any]] = [
        {"id": 1, "name": "Festivals"},
        {"id": 2, "name": "Folk Songs"},
        {"id": 3, "name": "Photos"},
        {"id": 4, "name": "Oral Histories"},
    ]
    _demo_records: List[Dict[str, Any]] = [
        {
            "id": 101, "title": "Bathukamma Procession",
            "description": "Floral stacks carried during Bathukamma.",
            "category_id": 1, "language": "telugu",
            "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/a/a4/Bathukamma_festival.jpg",
            "tags": ["festival","bathukamma"],
            "location": {"latitude": 17.385, "longitude": 78.487},
        },
        {
            "id": 102, "title": "Bonalu Offerings",
            "description": "Traditional offerings to the Goddess during Bonalu.",
            "category_id": 1, "language": "telugu",
            "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Bonalu_festival.jpg",
            "tags": ["festival","bonalu"],
            "location": {"latitude": 17.406, "longitude": 78.477},
        },
    ]

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._token: Optional[str] = None

    # ------------ internals ------------
    @property
    def base(self) -> str:
        return API_BASE.rstrip("/")

    def _with_auth(self) -> None:
        if self._token:
            self.session.headers.update({"Authorization": f"Bearer {self._token}"})
        else:
            self.session.headers.pop("Authorization", None)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        retry_on: Tuple[int, ...] = (502, 503, 504),
    ) -> Optional[requests.Response]:
        """HTTP with tiny retry on transient errors."""
        self._with_auth()
        url = f"{self.base}{path}"
        tries = 0
        while True:
            try:
                resp = self.session.request(
                    method.upper(), url,
                    params=params, json=json, data=data, files=files,
                    timeout=timeout or REQ_TIMEOUT,
                )
                if resp.status_code in retry_on and tries < MAX_RETRIES:
                    tries += 1
                    time.sleep(RETRY_BACKOFF)
                    continue
                return resp if resp.ok else None
            except (requests.Timeout, requests.ConnectionError):
                if tries < MAX_RETRIES:
                    tries += 1
                    time.sleep(RETRY_BACKOFF)
                    continue
                return None
            except requests.RequestException:
                return None

    # ------------- auth -------------
    def set_auth_token(self, token: str) -> None:
        self._token = token
        self._with_auth()

    def login_for_access_token(self, phone_or_username: str, password: str) -> Optional[Dict[str, Any]]:
        if DEMO_MODE:
            if password == "demo123":
                tok = "demo-token-123"
                self.set_auth_token(tok)
                self.session.headers.update({"X-Demo": "1"})
                return {"access_token": tok, "token_type": "bearer"}
            return None
        resp = self._request("POST", "/login", json={"username": phone_or_username, "password": password})
        if not resp:
            resp = self._request("POST", "/login", data={"username": phone_or_username, "password": password})
        if not resp:
            resp = self._request("POST", "/login", json={"phone": phone_or_username, "password": password})
        if not resp:
            return None
        data = resp.json()
        tok = data.get("access_token")
        if tok:
            self.set_auth_token(tok)
        return data

    def read_users_me(self) -> Optional[Dict[str, Any]]:
        if DEMO_MODE:
            return {"id": 101, "full_name": "Demo User", "phone": "demo", "email": "demo@swecha.org"} if self._token else None
        resp = self._request("GET", "/auth/me")
        return resp.json() if resp else None

    # --------- categories ----------
    def get_categories(self) -> List[Dict[str, Any]]:
        if DEMO_MODE:
            return list(self._demo_categories)
        resp = self._request("GET", "/categories/")
        if not resp:
            return []
        data = resp.json()
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
        return data if isinstance(data, list) else []

    # --------- records (read/search) ----------
    def get_records(self, *, page: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if DEMO_MODE:
            return list(self._demo_records)
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        resp = self._request("GET", "/records/", params=params or None)
        return resp.json() if resp else []

    def search_records(self, q: str, *, page: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if DEMO_MODE:
            ql = (q or "").lower()
            return [r for r in self._demo_records if ql in (r.get("title","").lower() + " " + " ".join(r.get("tags",[])))]
        params: Dict[str, Any] = {"q": q}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        resp = self._request("GET", "/records/search", params=params)
        return resp.json() if resp else []

    def search_records_nearby(
        self, *, latitude: float, longitude: float, radius_km: float = 10.0,
        page: Optional[int] = None, limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"latitude": latitude, "longitude": longitude, "radius_km": radius_km}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        resp = self._request("GET", "/records/search/nearby", params=params)
        return resp.json() if resp else []

    # --------- records (create + chunk upload) ----------
    def create_record(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if DEMO_MODE:
            new_id = max((r["id"] for r in self._demo_records), default=100) + 1
            rec = {"id": new_id, **payload}
            self._demo_records.insert(0, rec)
            return rec
        resp = self._request("POST", "/records/upload", json=payload, timeout=max(REQ_TIMEOUT, 30))
        return resp.json() if resp else None

    def upload_file_chunk(
        self, *, upload_uuid: str, filename: str, chunk_bytes: bytes,
        chunk_index: int, total_chunks: int, mime: str = "application/octet-stream",
    ) -> bool:
        if DEMO_MODE:
            return True
        files = {"file": (filename, chunk_bytes, mime)}
        data = {"upload_uuid": upload_uuid, "chunk_index": str(chunk_index), "total_chunks": str(total_chunks)}
        resp = self._request("POST", "/records/upload/chunk", data=data, files=files, timeout=max(REQ_TIMEOUT, 60))
        return bool(resp)

    # --------- utility ----------
    @staticmethod
    def chunk_file(content: bytes, *, chunk_size: int = 1024 * 1024) -> List[bytes]:
        return [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
