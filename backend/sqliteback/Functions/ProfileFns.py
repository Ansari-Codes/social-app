import datetime
import threading
import time
from typing import Literal, Optional, cast

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB, Profile, User
from backend.sqliteback.Functions.ChipFns import ChipFns

_PROFILE_CACHE: dict[tuple[int, Optional[int]], tuple[float, dict]] = {}
_PROFILE_CACHE_LOCK = threading.Lock()
_PROFILE_CACHE_TTL = 10.0


def invalidate_profile_cache(user_id: Optional[int] = None) -> None:
    with _PROFILE_CACHE_LOCK:
        if user_id is None:
            _PROFILE_CACHE.clear()
        else:
            to_del = [k for k in _PROFILE_CACHE if k[0] == user_id or k[1] == user_id]
            for k in to_del:
                _PROFILE_CACHE.pop(k, None)


def compose_profile(
    user: User,
    profile: Optional[Profile],
    *,
    viewer_user_id: Optional[int] = None,
    relationship_stats: Optional[dict] = None,
) -> dict:
    """Shape a database record into the client-safe profile payload."""
    if user.id is None:
        raise ValueError("Cannot compose a profile for a user without an id.")
    profile_data = profile or Profile(user_id=user.id)
    is_owner = viewer_user_id is not None and user.id is not None and user.id == viewer_user_id

    return {
        "id": profile_data.id,
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email if is_owner else None,
        "about": profile_data.about,
        "powerline": profile_data.powerline,
        "banner_color": profile_data.banner_color,
        "emoji": profile_data.emoji,
        "phone": profile_data.phone if is_owner else None,
        "birthday": profile_data.birthday,
        "is_owner": is_owner,
        **(relationship_stats or {}),
    }


class ProfileFns:
    def __init__(self, db: Database = DB):
        self.users = db.use("users")
        self.profiles = db.use("profiles")
        self.chips = ChipFns(db)

    def ensure_for_user(self, user_id: int) -> Profile:
        existing = self.profiles.query().where(user_id=user_id).first()
        if existing is not None:
            return cast(Profile, existing.to_model())

        profile = Profile(user_id=user_id)
        self.profiles.insert(profile)
        created = self.profiles.query().where(user_id=user_id).first()
        if created is None:
            raise ValueError(f"Profile for user {user_id} could not be created.")
        return cast(Profile, created.to_model())

    def read_for_user(
        self,
        user_id: int,
        *,
        viewer_user_id: Optional[int] = None,
        prefetched_user: Optional[User] = None,
    ) -> Optional[dict]:
        now = time.monotonic()
        cache_key = (user_id, viewer_user_id)
        with _PROFILE_CACHE_LOCK:
            cached = _PROFILE_CACHE.get(cache_key)
            if cached is not None and now < cached[0]:
                return dict(cached[1])

        if prefetched_user is not None and prefetched_user.id == user_id:
            user = prefetched_user
        else:
            user_record = self.users.get(user_id)
            if user_record is None:
                return None
            user = cast(User, user_record.to_model())

        profile_row = self.profiles.query().where(user_id=user_id).first()
        profile = (
            cast(Profile, profile_row.to_model())
            if profile_row is not None
            else self.ensure_for_user(user_id)
        )
        profile_map = {user_id: profile} if profile is not None else None
        result = compose_profile(
            user,
            profile,
            viewer_user_id=viewer_user_id,
            relationship_stats=self.chips.profile_state(
                viewer_user_id, user_id, profiles_by_user_id=profile_map
            ),
        )
        with _PROFILE_CACHE_LOCK:
            _PROFILE_CACHE[cache_key] = (now + _PROFILE_CACHE_TTL, result)
        return result

    def read_by_username(
        self,
        username: str,
        *,
        viewer_user_id: Optional[int] = None,
    ) -> Optional[dict]:
        user_record = self.users.query().where(username=username.strip()).first()
        if user_record is None:
            return None
        user = cast(User, user_record.to_model())
        if user.id is None:
            return None
        return self.read_for_user(user.id, viewer_user_id=viewer_user_id)

    def update_for_user(self, user_id: int, **fields) -> Optional[dict]:
        user_record = self.users.get(user_id)
        if user_record is None:
            return None

        profile = self.profiles.query().where(user_id=user_id).first()
        if profile is None:
            profile = self.ensure_for_user(user_id)

        allowed = {
            "about",
            "powerline",
            "banner_color",
            "emoji",
            "phone",
            "birthday",
        }
        safe_fields = {key: value for key, value in fields.items() if key in allowed}
        if not safe_fields:
            return self.read_for_user(user_id, viewer_user_id=user_id)

        safe_fields["updated_at"] = datetime.datetime.now()
        self.profiles.query().where(user_id=user_id).update(**safe_fields)
        invalidate_profile_cache(user_id)
        return self.read_for_user(user_id, viewer_user_id=user_id)

    def set_profile_chip(
        self,
        viewer_user_id: int,
        target_user_id: int,
        kind: Literal["follow", "star"],
        enabled: bool,
    ) -> Optional[dict]:
        self.chips.set_profile_chip(viewer_user_id, target_user_id, kind, enabled)
        invalidate_profile_cache(target_user_id)
        invalidate_profile_cache(viewer_user_id)
        return self.read_for_user(target_user_id, viewer_user_id=viewer_user_id)

    def toggle_profile_reaction(
        self,
        viewer_user_id: int,
        target_user_id: int,
        reaction: str,
    ) -> Optional[dict]:
        self.chips.toggle_profile_reaction(viewer_user_id, target_user_id, reaction)
        invalidate_profile_cache(target_user_id)
        invalidate_profile_cache(viewer_user_id)
        return self.read_for_user(target_user_id, viewer_user_id=viewer_user_id)

    def list_connections(
        self,
        user_id: int,
        viewer_user_id: int,
        direction: Literal["followers", "following"],
    ) -> list[dict]:
        connection_ids = self.chips.connection_profile_ids(user_id, direction)
        profiles = []
        for profile_id in connection_ids:
            profile_row = self.profiles.get(profile_id)
            if profile_row is None:
                continue
            profile = cast(Profile, profile_row.to_model())
            user_row = self.users.get(profile.user_id)
            if user_row is None:
                continue
            user = cast(User, user_row.to_model())
            profiles.append(
                compose_profile(
                    user,
                    profile,
                    viewer_user_id=viewer_user_id,
                    relationship_stats=self.chips.profile_state(viewer_user_id, profile.user_id),
                )
            )
        return profiles
