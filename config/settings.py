import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # Use real Swecha API base later; local dummy now
    API_BASE: str = os.getenv("SWECHA_API_BASE", "http://localhost:8000")
    API_TIMEOUT: int = int(os.getenv("SWECHA_API_TIMEOUT", "20"))

settings = Settings()
