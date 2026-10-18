"""
Security/Auth.py — Bearer-token authentication dependency.

Reads the token from the Authorization header, looks it up in the sessions
table, and returns the owning User. Raises 401 on any failure.
"""

import datetime
from typing import Optional, cast

from fastapi import Depends, HTTPException, Request, status

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.SessionFns import SessionFns


def _extract_bearer(request: Request) -> str:
    header = request.headers.get("Authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = token.strip()
    if not token or len(token) > 256 or any(char.isspace() for char in token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


import threading
import time

# In-memory authentication cache: token -> (User, session_id, expires_at, cached_at)
_AUTH_CACHE: dict[str, tuple[User, int, datetime.datetime, float]] = {}
_AUTH_CACHE_LOCK = threading.Lock()
_AUTH_CACHE_TTL = 60.0  # seconds


def invalidate_auth_cache(token: str | None = None, user_id: int | None = None) -> None:
    """Invalidate cached session entries on logout, password change, or profile update."""
    with _AUTH_CACHE_LOCK:
        if token is not None:
            _AUTH_CACHE.pop(token, None)
        elif user_id is not None:
            keys_to_remove = [k for k, v in _AUTH_CACHE.items() if v[0].id == user_id]
            for k in keys_to_remove:
                _AUTH_CACHE.pop(k, None)
        else:
            _AUTH_CACHE.clear()


def get_current_user(request: Request) -> User:
    """
    FastAPI dependency. Returns the authenticated User or raises 401.
    Uses in-memory caching to prevent redundant database round-trips.
    """
    token = _extract_bearer(request)

    now_monotonic = time.monotonic()
    with _AUTH_CACHE_LOCK:
        cached = _AUTH_CACHE.get(token)

    if cached is not None:
        user, session_id, expires_at, cached_at = cached
        now_dt = datetime.datetime.now(expires_at.tzinfo)
        if expires_at > now_dt and (now_monotonic - cached_at) < _AUTH_CACHE_TTL:
            request.state.session_id = session_id
            return user

    users = DB.use("users")
    session = SessionFns(DB).read_by_token(token)
    if session is None or session.revoked:
        invalidate_auth_cache(token=token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Expiry check
    try:
        expires_at = session.expires_at
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has no valid expiry.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    now = datetime.datetime.now(expires_at.tzinfo)
    if expires_at <= now:
        invalidate_auth_cache(token=token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_row = users.get(session.user_id)
    if user_row is None:
        invalidate_auth_cache(token=token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session owner no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = cast(User, user_row.to_model())
    if not user.is_active:
        invalidate_auth_cache(token=token)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    with _AUTH_CACHE_LOCK:
        if len(_AUTH_CACHE) > 2000:
            _AUTH_CACHE.clear()
        _AUTH_CACHE[token] = (user, session.id, expires_at, now_monotonic)

    request.state.session_id = session.id
    return user


def get_optional_current_user(request: Request) -> Optional[User]:
    """Return an authenticated user when available, otherwise treat the request as public."""
    if not request.headers.get("Authorization"):
        return None
    try:
        return get_current_user(request)
    except HTTPException as error:
        if error.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
            return None
        raise


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Convenience dependency: current user must be an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return user