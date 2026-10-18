"""
Models/SessionModels.py — Request / response schemas for session endpoints.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ReqLogin(BaseModel):
    """Payload for POST /sessions/login.

    Caller may identify by either username or email.
    """

    model_config = ConfigDict(extra="forbid")

    username: Optional[str] = Field(default=None, min_length=1, max_length=64)
    email: Optional[str] = Field(default=None, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ReqLogout(BaseModel):
    """Optional body for POST /sessions/logout."""

    model_config = ConfigDict(extra="forbid")

    all_devices: bool = False


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class SessionPublic(BaseModel):
    """A session as seen by its owner (token included only on login)."""

    id: int
    user_id: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str
    expires_at: str
    revoked: bool


class DataLogin(BaseModel):
    token: str
    expires_at: str
    session: SessionPublic


class DataSession(BaseModel):
    session: SessionPublic


class DataSessions(BaseModel):
    sessions: list[SessionPublic]


class DataLogout(BaseModel):
    revoked: int
    all_devices: bool = False