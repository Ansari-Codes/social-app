"""Shared FastAPI application lifecycle for PostgreSQL-backed providers."""

from contextlib import asynccontextmanager
import logging
import os
import time
from typing import cast
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg_pool import PoolTimeout

from backend.sqliteback.Database.core import Database
from backend.sqliteback.config import SLOW_REQUEST_LOG_MS

DEFAULT_CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
request_logger = logging.getLogger("silence.request")


def parse_cors_origins(value: str | None = None) -> list[str]:
    configured = os.getenv("B_CORS_ORIGINS") if value is None else value
    if configured is None:
        return list(DEFAULT_CORS_ORIGINS)

    origins: list[str] = []
    for entry in configured.split(","):
        origin = entry.strip().rstrip("/")
        if not origin:
            continue
        parsed = urlsplit(origin)
        if (
            origin == "*"
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ValueError("B_CORS_ORIGINS must contain explicit HTTP(S) origins only.")
        if origin not in origins:
            origins.append(origin)

    if not origins:
        raise ValueError("B_CORS_ORIGINS must contain at least one origin.")
    return origins


def create_postgres_app(database, auto_migrate: bool) -> FastAPI:
    import backend.sqliteback.Database.db as database_module

    database_module.DB = database

    from backend.sqliteback.Functions.SessionFns import SessionFns
    from backend.sqliteback.Helpers import AuthHelp
    from backend.sqliteback.Routes.AnalyticsRts import analytics_router
    from backend.sqliteback.Routes.FeedRts import feed_router
    from backend.sqliteback.Routes.NotificationRts import notifications_router
    from backend.sqliteback.Routes.ProfileRts import profiles_router
    from backend.sqliteback.Routes.PostRts import posts_router
    from backend.sqliteback.Routes.SessionRts import sessions_router
    from backend.sqliteback.Routes.UserRts import users_router

    AuthHelp.DB = database

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            if auto_migrate:
                database.initialize()
            else:
                database.check()
            sessions = SessionFns(cast(Database, database))
            sessions.migrate_plaintext_tokens()
            sessions.purge_expired()
            yield
        finally:
            database.close()

    app = FastAPI(title="Silence", lifespan=lifespan)

    @app.exception_handler(PoolTimeout)
    async def handle_pool_timeout(_request, _error):
        request_logger.warning("database_pool_timeout")
        return JSONResponse(
            status_code=503,
            content={"detail": "Database is busy. Please retry shortly."},
            headers={"Retry-After": "1"},
        )

    @app.middleware("http")
    async def log_slow_requests(request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if elapsed_ms >= SLOW_REQUEST_LOG_MS:
            request_logger.warning(
                "slow_request method=%s path=%s status=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        return response

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=parse_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )
    app.include_router(users_router)
    app.include_router(profiles_router)
    app.include_router(posts_router)
    app.include_router(feed_router)
    app.include_router(notifications_router)
    app.include_router(analytics_router)
    app.include_router(sessions_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def readiness():
        try:
            if database.check():
                return {"status": "ready"}
        except Exception:
            pass
        return JSONResponse(status_code=503, content={"status": "not_ready"})

    return app