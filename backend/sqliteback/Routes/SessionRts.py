"""
Routes/SessionRts.py — HTTP endpoints for sessions.

Auth matrix:
    POST   /sessions/login       public
    POST   /sessions/logout      bearer
    POST   /sessions/logout-all  bearer
    GET    /sessions/me          bearer
    GET    /sessions/            bearer (own sessions only)
    DELETE /sessions/{id}        bearer (own sessions only)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.sqliteback.Database.db import DB, Session, User
from backend.sqliteback.Functions.SessionFns import SessionFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user, invalidate_auth_cache
from backend.sqliteback.Models.core import BaseResponse
from backend.sqliteback.Models.SessionModels import (
    DataLogin,
    DataLogout,
    DataSession,
    DataSessions,
    ReqLogin,
    ReqLogout,
    SessionPublic,
)

sessions_router = APIRouter(prefix="/sessions", tags=["session"])
sessions_fns = SessionFns(DB)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _public(s: Session) -> SessionPublic:
    return SessionPublic(
        id=s.id,  # type: ignore[arg-type]
        user_id=s.user_id,
        user_agent=s.user_agent,
        ip_address=s.ip_address,
        created_at=s.created_at.isoformat(),
        expires_at=s.expires_at.isoformat(),
        revoked=s.revoked,
    )


def _client_ua_ip(request: Request) -> tuple[Optional[str], Optional[str]]:
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return ua, ip


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------

@sessions_router.post("/login", response_model=BaseResponse[DataLogin])
def login(body: ReqLogin, request: Request):
    """Exchange credentials for a bearer token."""
    if not body.username and not body.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either 'username' or 'email'.",
        )

    ua, ip = _client_ua_ip(request)

    session = sessions_fns.login(
        username=body.username,
        email=body.email,
        password=body.password,
        user_agent=ua,
        ip_address=ip,
    )

    if session is None:
        # Generic message — never reveal which field was wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = DataLogin(
        token=session.token,
        expires_at=session.expires_at.isoformat(),
        session=_public(session),
    )
    return BaseResponse[DataLogin](data=payload)


@sessions_router.post("/logout", response_model=BaseResponse[DataLogout])
def logout(
    request: Request,
    body: Optional[ReqLogout] = None,
    me: User = Depends(get_current_user),
):
    """Revoke the caller's current session, or all their sessions."""
    all_devices = bool(body and body.all_devices)

    if all_devices:
        n = sessions_fns.revoke_all_for_user(me.id)  # type: ignore[arg-type]
    else:
        session_id = getattr(request.state, "session_id", None)
        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session context missing.",
            )
        n = sessions_fns.revoke(session_id)

    invalidate_auth_cache()

    return BaseResponse[DataLogout](
        data=DataLogout(revoked=n, all_devices=all_devices)
    )


# ---------------------------------------------------------------------------
# Current session
# ---------------------------------------------------------------------------

@sessions_router.get("/me", response_model=BaseResponse[DataSession])
def get_my_session(
    request: Request,
    me: User = Depends(get_current_user),
):
    session_id = getattr(request.state, "session_id", None)
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session context missing.",
        )
    session = sessions_fns.read(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session no longer exists.",
        )
    return BaseResponse[DataSession](data=DataSession(session=_public(session)))


# ---------------------------------------------------------------------------
# Listing / deleting own sessions
# ---------------------------------------------------------------------------

@sessions_router.get("/", response_model=BaseResponse[DataSessions])
def list_my_sessions(
    include_revoked: bool = False,
    include_expired: bool = False,
    me: User = Depends(get_current_user),
):
    sessions = sessions_fns.read_many(
        me.id,  # type: ignore[arg-type]
        include_revoked=include_revoked,
        include_expired=include_expired,
    )
    return BaseResponse[DataSessions](
        data=DataSessions(sessions=[_public(s) for s in sessions])
    )


@sessions_router.delete("/{session_id}", response_model=BaseResponse[DataLogout])
def revoke_session(
    session_id: int,
    me: User = Depends(get_current_user),
):
    """Revoke one of the caller's own sessions."""
    session = sessions_fns.read(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )
    if session.user_id != me.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke your own sessions.",
        )
    sessions_fns.revoke(session_id)
    return BaseResponse[DataLogout](
        data=DataLogout(revoked=1, all_devices=False)
    )