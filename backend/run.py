"""Run the configured backend for local use or a hosted Python service."""

import os

import uvicorn


BACKEND_APPS = {
    "sqlite": "backend.sqliteback.main:app",
    "supabase": "backend.supaback.main:app",
    "neon": "backend.neonback.main:app",
}


def main() -> None:
    backend = os.getenv("B_BACKEND", "sqlite").strip().lower()
    app = BACKEND_APPS.get(backend)
    if app is None:
        options = ", ".join(BACKEND_APPS)
        raise SystemExit(f"B_BACKEND must be one of: {options}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
    )


if __name__ == "__main__":
    main()