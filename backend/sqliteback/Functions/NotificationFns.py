import datetime
import threading
import time
from typing import Optional

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB, Notification, Post, Profile, User

_NOTIF_CACHE: dict[int, tuple[float, list[dict]]] = {}
_NOTIF_CACHE_LOCK = threading.Lock()
_NOTIF_CACHE_TTL = 8.0


def invalidate_notifications_cache(user_id: Optional[int] = None) -> None:
    with _NOTIF_CACHE_LOCK:
        if user_id is None:
            _NOTIF_CACHE.clear()
        else:
            _NOTIF_CACHE.pop(user_id, None)


class NotificationFns:
    def __init__(self, db: Database = DB):
        self.db = db
        self.notifications = db.use("notifications")
        self.users = db.use("users")
        self.profiles = db.use("profiles")
        self.posts = db.use("posts")

    def notify(
        self,
        recipient_user_id: int,
        kind: str,
        content: str,
        *,
        actor_user_id: Optional[int] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
    ) -> Optional[int]:
        """Persist a notification; self-notifications are intentionally skipped."""
        if actor_user_id == recipient_user_id:
            return None
        if self.users.get(recipient_user_id) is None:
            raise LookupError("Notification recipient not found.")

        actor_profile_id = None
        if actor_user_id is not None:
            actor_profile = self.profiles.query().where(user_id=actor_user_id).first()
            if actor_profile is not None:
                actor_profile_id = actor_profile.id

        inserted_id = self.notifications.insert(
            Notification(
                user_id=recipient_user_id,
                actor_profile_id=actor_profile_id,
                kind=kind,
                content=content.strip()[:500],
                target_type=target_type,
                target_id=target_id,
            )
        )
        invalidate_notifications_cache(recipient_user_id)
        return inserted_id

    def _public(
        self,
        notification: Notification,
        *,
        profiles_by_id: Optional[dict[int, Profile]] = None,
        users_by_id: Optional[dict[int, User]] = None,
        posts_by_id: Optional[dict[int, Post]] = None,
    ) -> dict:
        actor_username = None
        actor_display_name = None
        actor_emoji = None
        if notification.actor_profile_id is not None:
            if profiles_by_id is not None:
                profile = profiles_by_id.get(notification.actor_profile_id)
            else:
                profile_row = self.profiles.get(notification.actor_profile_id)
                profile = profile_row.to_model() if profile_row is not None else None

            if profile is not None:
                if users_by_id is not None:
                    user = users_by_id.get(profile.user_id)
                else:
                    user_row = self.users.get(profile.user_id)
                    user = user_row.to_model() if user_row is not None else None
                if user is not None:
                    actor_username = user.username
                    actor_display_name = user.display_name
                actor_emoji = profile.emoji

        target_post_id = None
        target_post_snippet = None
        if notification.target_type in ("post", "comment") and notification.target_id is not None:
            if posts_by_id is not None:
                post = posts_by_id.get(notification.target_id)
            else:
                post_row = self.posts.get(notification.target_id)
                post = post_row.to_model() if post_row is not None else None

            if post is not None:
                clean_content = " ".join(post.content.split())
                target_post_snippet = clean_content[:90] + ("..." if len(clean_content) > 90 else "")
                target_post_id = post.reply_to if (post.is_comment and post.reply_to is not None) else post.id

        return {
            "id": notification.id,
            "kind": notification.kind,
            "content": notification.content,
            "actor_profile_id": notification.actor_profile_id,
            "actor_username": actor_username,
            "actor_display_name": actor_display_name,
            "actor_emoji": actor_emoji,
            "target_type": notification.target_type,
            "target_id": notification.target_id,
            "target_post_id": target_post_id,
            "target_post_snippet": target_post_snippet,
            "is_read": notification.read_at is not None,
            "created_at": notification.created_at.isoformat(),
        }

    def list_for_user(self, user_id: int, limit: int = 50) -> list[dict]:
        now = time.monotonic()
        if limit == 50:
            with _NOTIF_CACHE_LOCK:
                cached = _NOTIF_CACHE.get(user_id)
                if cached is not None and now < cached[0]:
                    return [dict(item) for item in cached[1]]

        rows = self.notifications.query().where(user_id=user_id).order_by(
            "created_at", desc=True
        ).limit(max(1, min(limit, 100))).all()
        if not rows:
            if limit == 50:
                with _NOTIF_CACHE_LOCK:
                    _NOTIF_CACHE[user_id] = (now + _NOTIF_CACHE_TTL, [])
            return []

        notifications = [row.to_model() for row in rows]

        actor_profile_ids = list({
            n.actor_profile_id for n in notifications if n.actor_profile_id is not None
        })
        profiles_by_id: dict[int, Profile] = {}
        users_by_id: dict[int, User] = {}
        if actor_profile_ids:
            p_rows = self.profiles.query().where(id=actor_profile_ids).all()
            profiles_by_id = {row.id: row.to_model() for row in p_rows}
            user_ids = list({p.user_id for p in profiles_by_id.values() if p.user_id is not None})
            if user_ids:
                u_rows = self.users.query().where(id=user_ids).all()
                users_by_id = {row.id: row.to_model() for row in u_rows}

        target_post_ids = list({
            n.target_id
            for n in notifications
            if n.target_type in ("post", "comment") and n.target_id is not None
        })
        posts_by_id: dict[int, Post] = {}
        if target_post_ids:
            post_rows = self.posts.query().where(id=target_post_ids).all()
            posts_by_id = {row.id: row.to_model() for row in post_rows}

        result = [
            self._public(
                n,
                profiles_by_id=profiles_by_id,
                users_by_id=users_by_id,
                posts_by_id=posts_by_id,
            )
            for n in notifications
        ]
        if limit == 50:
            with _NOTIF_CACHE_LOCK:
                _NOTIF_CACHE[user_id] = (now + _NOTIF_CACHE_TTL, result)
        return result

    def unread_count(self, user_id: int) -> int:
        now = time.monotonic()
        with _NOTIF_CACHE_LOCK:
            cached = _NOTIF_CACHE.get(user_id)
            if cached is not None and now < cached[0]:
                return sum(1 for n in cached[1] if not n.get("is_read"))
        return self.notifications.query().where(user_id=user_id, read_at=None).count()

    def mark_read(self, user_id: int, notification_id: int) -> bool:
        row = self.notifications.query().where(
            id=notification_id,
            user_id=user_id,
        ).first()
        if row is None:
            return False
        if row.read_at is None:
            self.notifications.query().where(id=notification_id, user_id=user_id).update(
                read_at=datetime.datetime.now()
            )
        invalidate_notifications_cache(user_id)
        return True

    def mark_all_read(self, user_id: int) -> int:
        count = self.notifications.query().where(
            user_id=user_id,
            read_at=None,
        ).update(read_at=datetime.datetime.now())
        invalidate_notifications_cache(user_id)
        return count
