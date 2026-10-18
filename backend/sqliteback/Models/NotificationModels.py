"""
Models/NotificationModels.py — API shapes for in-app notifications.
"""

from typing import Optional

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: int
    kind: str
    content: str
    actor_profile_id: Optional[int] = None
    actor_username: Optional[str] = None
    actor_display_name: Optional[str] = None
    actor_emoji: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    target_post_id: Optional[int] = None
    target_post_snippet: Optional[str] = None
    is_read: bool
    created_at: str


class DataNotifications(BaseModel):
    notifications: list[NotificationPublic]
    unread_count: int


class DataOk(BaseModel):
    ok: bool = True
