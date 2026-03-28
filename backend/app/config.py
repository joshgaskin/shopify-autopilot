"""
Configuration — reads from .env in the repo root.

The backend is started via `cd backend && uvicorn app.main:app`,
so .env is at "../.env" relative to cwd. We check both locations
for flexibility.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Find .env: check parent dir first (repo root when run from backend/),
# then current dir (when run from repo root).
_backend_dir = Path(__file__).resolve().parent.parent  # backend/
_repo_root = _backend_dir.parent  # HackathonStarterRepo/

_env_file = None
if (_repo_root / ".env").exists():
    _env_file = str(_repo_root / ".env")
elif (Path.cwd() / ".env").exists():
    _env_file = str(Path.cwd() / ".env")
elif (Path.cwd().parent / ".env").exists():
    _env_file = str(Path.cwd().parent / ".env")


class Settings(BaseSettings):
    SHOPIFY_ACCESS_TOKEN: str
    SHOPIFY_STORE_URL: str
    SHOPIFY_API_VERSION: str = "2025-01"
    SIMULATOR_ENABLED: bool = True
    SIMULATOR_INTERVAL_MIN: int = 60
    SIMULATOR_INTERVAL_MAX: int = 180
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_repo_root}/hackathon.db"
    ANTHROPIC_API_KEY: str = ""
    AGENT_LOOP_INTERVAL: int = 60  # seconds between autonomous agent cycles

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
