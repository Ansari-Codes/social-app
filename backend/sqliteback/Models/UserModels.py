"""
Models/UserModels.py — Request / response schemas for user endpoints.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ReqGetMany(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    username: Optional[str] = None


class ReqCreateUser(BaseModel):
    """Payload for public POST /users/ (registration)."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=128)
    # NOTE: `is_admin` intentionally omitted — cannot self-elevate.


class ReqUpdateMe(BaseModel):
    """Payload for PATCH /users/me — user updating their own identity and presentation."""

    model_config = ConfigDict(extra="forbid")

    username: Optional[str] = Field(default=None, min_length=3, max_length=64)
    display_name: Optional[str] = Field(default=None, max_length=128)
    email: Optional[EmailStr] = None
    # password handled by a separate endpoint below


class ReqChangePassword(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ReqUpdateUser(BaseModel):
    """Payload for PATCH /users/{id} — admin editing another user."""

    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(default=None, max_length=128)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class ReqDeleteSelf(BaseModel):
    """Payload for DELETE /users/me — requires password confirmation."""

    model_config = ConfigDict(extra="forbid")

    password: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserPublic(BaseModel):
    """User shape returned to clients (never includes password_hash)."""

    id: int
    username: str
    email: str
    display_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: str
    updated_at: str
    last_login: Optional[str] = None


class DataGetMany(BaseModel):
    users: list[UserPublic]


class DataUser(BaseModel):
    user: UserPublic


# Backwards-compatible alias — routes originally used DataUserCreated
DataUserCreated = DataUser


class DataOk(BaseModel):
    ok: bool = True