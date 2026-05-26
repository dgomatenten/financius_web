import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DEFAULT_LOG_FILE = str(Path(__file__).resolve().parents[2] / "logs" / "app.log")


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    jwt_secret: str
    google_client_id: str
    google_client_secret: str
    allowed_origins: str
    qr_pairing_token_ttl_seconds: int
    api_base_url: str
    backend_port: int
    flask_env: str
    log_file: str
    sync_max_payload_bytes: int
    sync_max_items_per_request: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/financius.db"),
        secret_key=os.getenv("SECRET_KEY", "replace-me"),
        jwt_secret=os.getenv("JWT_SECRET", "replace-me"),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", "replace-me"),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "replace-me"),
        allowed_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8000"),
        qr_pairing_token_ttl_seconds=int(os.getenv("QR_PAIRING_TOKEN_TTL_SECONDS", "300")),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        backend_port=int(os.getenv("BACKEND_PORT", "8000")),
        flask_env=os.getenv("FLASK_ENV", "development"),
        log_file=os.getenv("LOG_FILE", _DEFAULT_LOG_FILE),
        sync_max_payload_bytes=int(os.getenv("SYNC_MAX_PAYLOAD_BYTES", str(10 * 1024 * 1024))),
        sync_max_items_per_request=int(os.getenv("SYNC_MAX_ITEMS_PER_REQUEST", "1500")),
    )
