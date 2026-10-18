"""Neon PostgreSQL database instance using the shared adapter."""

from backend.supaback.Database.db import create_database

DB = create_database("B_NEON_DB_URL", "B_NEON_DB_PASS", "Neon")