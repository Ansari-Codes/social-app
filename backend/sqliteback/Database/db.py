"""
Database/db.py — Pydantic models, tables, and the shared Database instance.
"""

import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.sqliteback.Database.core import Database, Table
from backend.sqliteback.config import SQLITE_DB_PATH


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class User(BaseModel):
    """A registered account in the system."""

    id: Optional[int] = Field(
        default=None,
        description="Auto-incrementing primary key.",
        json_schema_extra={"primary_key": True, "autoincrement": True},
    )
    username: str = Field(
        description="Unique login handle (case-sensitive).",
        json_schema_extra={"unique": True},
    )
    email: str = Field(
        description="Unique email address used for login and notifications.",
        json_schema_extra={"unique": True},
    )
    password_hash: str = Field(
        description="Salted hash of the user's password. Never store plaintext.",
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Optional human-friendly name shown in the UI.",
    )
    is_active: bool = Field(
        default=True,
        description="False if the account has been deactivated or suspended.",
    )
    is_admin: bool = Field(
        default=False,
        description="True if the user has administrative privileges.",
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp when the account was created.",
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp of the last profile update.",
    )
    last_login: Optional[datetime.datetime] = Field(
        default=None,
        description="UTC timestamp of the most recent successful login.",
    )


class Session(BaseModel):
    """An active authentication session for a user."""

    id: Optional[int] = Field(
        default=None,
        description="Auto-incrementing primary key.",
        json_schema_extra={"primary_key": True, "autoincrement": True},
    )
    token: str = Field(
        description="Opaque bearer token identifying this session.",
        json_schema_extra={"unique": True},
    )
    user_id: int = Field(
        description="Foreign key referencing users.id — the session owner.",
        json_schema_extra={"references": "users(id)"},
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="Raw User-Agent header captured at session creation.",
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="IP address the session was created from.",
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp when the session was issued.",
    )
    expires_at: datetime.datetime = Field(
        description="UTC timestamp after which the session is no longer valid.",
    )
    revoked: bool = Field(
        default=False,
        description="True if the session was explicitly invalidated (logout).",
    )

class Profile(BaseModel):
    """Extended profile data for a user. One-to-one with users."""

    id: Optional[int] = Field(
        default=None,
        description="Auto-incrementing primary key.",
        json_schema_extra={"primary_key": True, "autoincrement": True},
    )
    user_id: int = Field(
        description="Foreign key referencing users.id — the owner.",
        json_schema_extra={"references": "users(id)", "unique": True},
    )
    about: Optional[str] = Field(
        default=None,
        description="Short bio or description shown on the profile.",
    )
    powerline: Optional[str] = Field(
        default=None,
        description="Status line — short message shown under the username.",
    )
    banner_color: Optional[str] = Field(
        default=None,
        description="Hex colour code for the profile banner, e.g. '#3B82F6'.",
    )
    emoji: Optional[str] = Field(
        default=None,
        description="Single emoji shown as the profile avatar.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Optional contact phone number.",
    )
    birthday: Optional[str] = Field(
        default=None,
        description="Birthday in ISO date format (YYYY-MM-DD).",
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp when the profile was created.",
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp of the last profile update.",
    )

class Post(BaseModel):
    """A post (or comment) made by a user."""

    id: Optional[int] = Field(
        default=None,
        description="Auto-incrementing primary key.",
        json_schema_extra={"primary_key": True, "autoincrement": True},
    )
    user_id: int = Field(
        description="Foreign key referencing users.id — the post owner.",
        json_schema_extra={"references": "users(id)"},
    )
    content: str = Field(
        description="Text body of the post.",
    )
    reply_to: Optional[int] = Field(
        default=None,
        description="Foreign key referencing posts.id — the post this replies to.",
        json_schema_extra={"references": "posts(id)"},
    )
    is_comment: bool = Field(
        default=False,
        description="True if this post is a comment on another post.",
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp when the post was created.",
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="UTC timestamp of the last post update.",
    )


class Chip(BaseModel):
    """A follow, profile star, or reaction attributed to a profile."""

    id: Optional[int] = Field(
        default=None,
        description="Auto-incrementing primary key.",
        json_schema_extra={"primary_key": True, "autoincrement": True},
    )
    chipped_to: int = Field(description="Target post or profile ID.")
    chipped_by: int = Field(
        description="Actor profile ID.",
        json_schema_extra={"references": "profiles(id)"},
    )
    kind: Literal["follow", "star", "reaction"] = Field(
        description="follow, star, or reaction."
    )
    content: str = Field(default="", description="Reaction text or optional chip content.")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Notification(BaseModel):
    """An in-app notification addressed to an account."""

    id: Optional[int] = Field(
        default=None,
        description="Auto-incrementing primary key.",
        json_schema_extra={"primary_key": True, "autoincrement": True},
    )
    user_id: int = Field(
        description="Notification recipient account ID.",
        json_schema_extra={"references": "users(id)"},
    )
    actor_profile_id: Optional[int] = Field(
        default=None,
        description="Profile that initiated the notification, if any.",
        json_schema_extra={"references": "profiles(id)"},
    )
    kind: str = Field(description="Event category, such as comment, reaction, follow, or star.")
    content: str = Field(description="Human-readable notification text.")
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    read_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


# ---------------------------------------------------------------------------
# Database instance
# ---------------------------------------------------------------------------

DB = Database(SQLITE_DB_PATH)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

users_table     = Table(User,     name="users")
sessions_table  = Table(Session,  name="sessions")
profiles_table  = Table(Profile,  name="profiles")
posts_table     = Table(Post,     name="posts")
chips_table     = Table(Chip,     name="chips")
notifications_table = Table(Notification, name="notifications")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

DB.create(
    users_table,
    sessions_table,
    profiles_table,
    posts_table,
    chips_table,
    notifications_table,
)


# ---------------------------------------------------------------------------
# Indexes and constraints the ORM doesn't emit automatically
# ---------------------------------------------------------------------------

DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_sessions_token   ON sessions(token)"
)
DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_sessions_user    ON sessions(user_id)"
)
DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id)"
)
DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_posts_user       ON posts(user_id)"
)
DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_posts_reply_to   ON posts(reply_to)"
)
DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_posts_feed_cursor ON posts(is_comment, id DESC)"
)
DB._execute(
    "CREATE INDEX IF NOT EXISTS idx_notifications_user_created "
    "ON notifications(user_id, created_at DESC)"
)
from backend.sqliteback.Database.migrations import create_chip_indexes, migrate_reactions_to_chips

create_chip_indexes(DB)
migrate_reactions_to_chips(DB)