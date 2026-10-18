"""FastAPI entrypoint for the Supabase PostgreSQL-backed API."""

from backend.postgres_app import create_postgres_app
from backend.sqliteback.config import DATABASE_AUTO_MIGRATE
from backend.supaback.Database.db import DB

app = create_postgres_app(DB, DATABASE_AUTO_MIGRATE)