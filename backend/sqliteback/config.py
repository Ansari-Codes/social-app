"""Shared settings loaded before either backend initializes its database."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

_sqlite_path = Path(os.getenv("B_SQLITE_DB_PATH", "AppData/db.sqlite"))
SQLITE_DB_PATH = _sqlite_path if _sqlite_path.is_absolute() else PROJECT_ROOT / _sqlite_path

SESSION_LIFETIME_DAYS = int(os.getenv("B_SESSION_LIFETIME_DAYS", "7"))
if SESSION_LIFETIME_DAYS < 1:
    raise ValueError("B_SESSION_LIFETIME_DAYS must be at least 1.")

DB_POOL_MIN_SIZE = int(os.getenv("B_DB_POOL_MIN_SIZE", "1"))
DB_POOL_MAX_SIZE = int(os.getenv("B_DB_POOL_MAX_SIZE", "5"))
DB_POOL_TIMEOUT_SECONDS = float(
    os.getenv("B_DB_POOL_TIMEOUT_SECONDS", "5")
)
DB_POOL_MAX_WAITING = int(os.getenv("B_DB_POOL_MAX_WAITING", "20"))
DATABASE_AUTO_MIGRATE = os.getenv("B_AUTO_MIGRATE", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
SLOW_REQUEST_LOG_MS = int(os.getenv("B_SLOW_REQUEST_LOG_MS", "750"))

if DB_POOL_MIN_SIZE < 0:
    raise ValueError("B_DB_POOL_MIN_SIZE cannot be negative.")
if DB_POOL_MAX_SIZE < 1 or DB_POOL_MIN_SIZE > DB_POOL_MAX_SIZE:
    raise ValueError("B_DB_POOL_MAX_SIZE must be positive and at least the minimum pool size.")
if DB_POOL_TIMEOUT_SECONDS <= 0:
    raise ValueError("B_DB_POOL_TIMEOUT_SECONDS must be positive.")
if DB_POOL_MAX_WAITING < 1:
    raise ValueError("B_DB_POOL_MAX_WAITING must be positive.")
if SLOW_REQUEST_LOG_MS < 1:
    raise ValueError("SLOW_REQUEST_LOG_MS must be positive.")