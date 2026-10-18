"""
Functions/UserFns.py — User domain logic on top of the ORM.
"""

import datetime
from typing import Optional

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB, Profile, User
from backend.sqliteback.Utils.Hashing import hash_password, verify_password


class UserFns:
    def __init__(self, db: Database = DB):
        self.database = db
        self.db = db.use("users")

    # ---- Create ------------------------------------------------------------
    def ensure_profile(self, user_id: int) -> Optional[Profile]:
        profiles = self.database.use("profiles")
        existing = profiles.query().where(user_id=user_id).first()
        if existing is not None:
            return existing.to_model()

        profile = Profile(user_id=user_id)
        profiles.insert(profile)
        return profiles.query().where(user_id=user_id).first().to_model()

    def create(self, user: User, password: str) -> Optional[User]:
        username = user.username.strip()
        email = user.email.strip().lower()

        if self.db.query().where(username=username).first() is not None:
            raise ValueError(f"Username '{username}' is already taken.")
        if self.db.query().where(email=email).first() is not None:
            raise ValueError(f"Email '{email}' is already registered.")

        user.username = username
        user.email = email
        user.password_hash = hash_password(password)

        user_id = self.db.insert(user)
        self.ensure_profile(user_id)
        return self.read(user_id)

    # ---- Read --------------------------------------------------------------
    def read(self, user_id: int) -> Optional[User]:
        rec = self.db.get(user_id)
        return rec.to_model() if rec else None

    def read_by_username(self, username: str) -> Optional[User]:
        rec = self.db.query().where(username=username.strip()).first()
        return rec.to_model() if rec else None

    def read_by_email(self, email: str) -> Optional[User]:
        rec = self.db.query().where(email=email.strip().lower()).first()
        return rec.to_model() if rec else None

    def read_many(self, **filters) -> list[User]:
        q = self.db.query()
        if filters:
            q = q.where(**filters)
        return [r.to_model() for r in q.all()]

    # ---- Update ------------------------------------------------------------
    def update(self, user: User) -> Optional[User]:
        """Persist changes made to a full User instance."""
        if user.id is None:
            raise ValueError("Cannot update a user without an id")
        changes = user.model_dump(exclude={"id", "created_at"})
        changes["updated_at"] = datetime.datetime.now()
        self.db.query().where(id=user.id).update(**changes)
        return self.read(user.id)

    def update_fields(self, user_id: int, **fields) -> Optional[User]:
        """
        Update only the given fields. Validates uniqueness for
        `username` / `email` if present.
        """
        if not fields:
            return self.read(user_id)

        if "username" in fields and fields["username"]:
            fields["username"] = fields["username"].strip()
            existing = self.db.query().where(username=fields["username"]).first()
            if existing is not None and existing.id != user_id:
                raise ValueError(f"Username '{fields['username']}' is already taken.")

        if "email" in fields and fields["email"]:
            fields["email"] = fields["email"].strip().lower()
            existing = self.db.query().where(email=fields["email"]).first()
            if existing is not None and existing.id != user_id:
                raise ValueError(f"Email '{fields['email']}' is already registered.")

        fields["updated_at"] = datetime.datetime.now()
        self.db.query().where(id=user_id).update(**fields)
        return self.read(user_id)

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        *,
        preserve_session_id: Optional[int] = None,
    ) -> None:
        user = self.read(user_id)
        if user is None:
            raise ValueError("User not found.")
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect.")
        self.db.query().where(id=user_id).update(
            password_hash=hash_password(new_password),
            updated_at=datetime.datetime.now(),
        )
        sessions = self.database.use("sessions")
        for session in sessions.query().where(user_id=user_id, revoked=False).all():
            if session.id != preserve_session_id:
                sessions.query().where(id=session.id).update(revoked=True)

    def touch_last_login(self, user_id: int) -> None:
        self.db.query().where(id=user_id).update(
            last_login=datetime.datetime.now(),
        )

    # ---- Delete ------------------------------------------------------------
    def delete(self, user_id: int) -> int:
        """Hard delete the user row. Cascades sessions manually."""
        # Revoke sessions first (in case FK cascade isn't configured)
        sessions = self.database.use("sessions")
        sessions.query().where(user_id=user_id).delete()
        return self.db.query().where(id=user_id).delete()

    def soft_delete(self, user_id: int) -> Optional[User]:
        """Deactivate the account without removing the row."""
        return self.update_fields(user_id, is_active=False)