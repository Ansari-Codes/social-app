"""
Functions/SessionFns.py — Session domain logic on top of the ORM.
"""

import datetime
import hashlib
import re
import secrets
from typing import Optional, cast

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB, Session, User
from backend.sqliteback.Functions.UserFns import UserFns
from backend.sqliteback.Utils.Hashing import hash_password, verify_password
from backend.sqliteback.config import SESSION_LIFETIME_DAYS

DEFAULT_LIFETIME_DAYS = SESSION_LIFETIME_DAYS
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


class SessionFns:
    def __init__(self, db: Database = DB, users: Optional[UserFns] = None):
        self.db = db.use("sessions")
        self.users = users or UserFns(db)

    @staticmethod
    def _token_digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def migrate_plaintext_tokens(self) -> int:
        """Hash session tokens created before at-rest hashing was introduced."""
        migrated = 0
        for record in self.db.query().all():
            token = str(record["token"])
            if re.fullmatch(r"[0-9a-f]{64}", token):
                continue
            self.db.query().where(id=int(record["id"])).update(
                token=self._token_digest(token)
            )
            migrated += 1
        return migrated

    # ---- Create ------------------------------------------------------------
    def issue(
        self,
        user_id: int,
        *,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        lifetime_days: int = DEFAULT_LIFETIME_DAYS,
    ) -> Session:
        """Create a fresh session for a user and return it."""
        token = secrets.token_urlsafe(32)
        now = datetime.datetime.now()
        session = Session(
            token=token,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=now,
            expires_at=now + datetime.timedelta(days=lifetime_days),
            revoked=False,
        )
        stored_session = session.model_copy(
            update={"token": self._token_digest(token)}
        )
        session.id = self.db.insert(stored_session)
        return session

    # ---- Login -------------------------------------------------------------
    def login(
        self,
        *,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        lifetime_days: int = DEFAULT_LIFETIME_DAYS,
    ) -> Optional[Session]:
        """
        Validate credentials and issue a session.

        Returns None on any credential failure (caller should return 401
        with a generic message — never reveal whether username or password
        was the wrong one).
        """
        if not username and not email:
            return None

        user: Optional[User] = None
        if username:
            user = self.users.read_by_username(username)
        if user is None and email:
            user = self.users.read_by_email(email)
        if user is None or not user.is_active:
            verify_password(password, _DUMMY_PASSWORD_HASH)
            return None

        if not verify_password(password, user.password_hash):
            return None

        session = self.issue(
            user.id,  # type: ignore[arg-type]
            user_agent=user_agent,
            ip_address=ip_address,
            lifetime_days=lifetime_days,
        )

        self.users.touch_last_login(user.id)  # type: ignore[arg-type]
        return session

    # ---- Read --------------------------------------------------------------
    def read(self, session_id: int) -> Optional[Session]:
        rec = self.db.get(session_id)
        return cast(Optional[Session], rec.to_model()) if rec else None

    def read_by_token(self, token: str) -> Optional[Session]:
        digest = self._token_digest(token)
        rec = self.db.query().where(token=digest).first()
        if rec is None:
            # Upgrade sessions created before tokens were hashed at rest.
            rec = self.db.query().where(token=token).first()
            if rec is None:
                return None
            legacy_session_id = int(rec["id"])
            self.db.query().where(id=legacy_session_id).update(token=digest)
            rec = self.db.get(legacy_session_id)
        return cast(Optional[Session], rec.to_model()) if rec else None

    def read_many(
        self,
        user_id: int,
        *,
        include_revoked: bool = False,
        include_expired: bool = False,
    ) -> list[Session]:
        q = self.db.query().where(user_id=user_id)
        if not include_revoked:
            q = q.where(revoked=False)

        sessions = [r.to_model() for r in q.all()]

        if not include_expired:
            now = datetime.datetime.now()
            sessions = [s for s in sessions if s.expires_at > now]

        return sessions

    # ---- Validity ----------------------------------------------------------
    @staticmethod
    def is_valid(session: Session) -> bool:
        if session.revoked:
            return False
        if session.expires_at <= datetime.datetime.now():
            return False
        return True

    # ---- Revoke ------------------------------------------------------------
    def revoke(self, session_id: int) -> int:
        return self.db.query().where(id=session_id).update(revoked=True)

    def revoke_by_token(self, token: str) -> int:
        session = self.read_by_token(token)
        return self.revoke(session.id) if session and session.id is not None else 0

    def revoke_all_for_user(self, user_id: int) -> int:
        return self.db.query().where(user_id=user_id, revoked=False).update(revoked=True)

    # ---- Cleanup -----------------------------------------------------------
    def purge_expired(self, user_id: Optional[int] = None) -> int:
        """Hard-delete expired or long-revoked sessions."""
        cutoff = datetime.datetime.now().isoformat()
        q = self.db.query()
        if user_id is not None:
            q = q.where(user_id=user_id)
        # Two passes: expired and revoked
        n = q.where_lt("expires_at", cutoff).delete()
        q2 = self.db.query()
        if user_id is not None:
            q2 = q2.where(user_id=user_id)
        n += q2.where(revoked=True).delete()
        return n