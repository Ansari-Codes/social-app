import unittest
import tempfile
import sqlite3
import datetime
from pathlib import Path

import hashlib
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from backend.sqliteback.Database.core import Database, Table
from backend.sqliteback.Database.db import Chip, Notification, Post, Profile, Session, User
from backend.sqliteback.Database.migrations import create_chip_indexes, migrate_reactions_to_chips
from backend.sqliteback.Functions.FeedFns import FeedFns
from backend.sqliteback.Functions.AnalyticsFns import AnalyticsFns
from backend.sqliteback.Functions.PostFns import PostFns
from backend.sqliteback.Functions.NotificationFns import NotificationFns
from backend.sqliteback.Functions.ProfileFns import ProfileFns
from backend.sqliteback.Functions.SessionFns import SessionFns
from backend.sqliteback.Functions.UserFns import UserFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user, get_optional_current_user
from backend.sqliteback.main import app, parse_cors_origins
from backend.sqliteback.Routes import PostRts
from backend.sqliteback.Routes import FeedRts
from backend.sqliteback.Routes import ProfileRts
from backend.sqliteback.Routes import NotificationRts
from backend.sqliteback.Routes import AnalyticsRts
from backend.sqliteback.Utils.Hashing import hash_password, verify_password


class PasswordHashTests(unittest.TestCase):
    def test_password_hash_uses_bounded_pbkdf2_work_factor(self):
        encoded = hash_password("Secret123!")
        self.assertEqual(encoded.split("$", 2)[1], "600000")
        self.assertTrue(verify_password("Secret123!", encoded))
        self.assertFalse(verify_password("wrong", encoded))
        self.assertFalse(
            verify_password("Secret123!", "pbkdf2_sha256$999999999$YWJj$YWJj")
        )


class TemporaryDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self._use_temporary_database()

    def _use_temporary_database(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db = Database(Path(self.temp_dir.name) / "tests.sqlite")
        self.addCleanup(self.db.close)
        self.db.create(
            Table(User, name="users"),
            Table(Session, name="sessions"),
            Table(Profile, name="profiles"),
            Table(Post, name="posts"),
            Table(Chip, name="chips"),
            Table(Notification, name="notifications"),
        )
        create_chip_indexes(self.db)

    def create_user(
        self,
        username: str,
        email: str,
        display_name: str | None = None,
    ) -> tuple[User, int]:
        user = UserFns(self.db).create(
            User(
                username=username,
                email=email,
                password_hash="",
                display_name=display_name,
            ),
            password="Secret123!",
        )
        if user is None or user.id is None:
            raise AssertionError("Test user was not created.")
        return user, user.id


class AuthSecurityTests(TemporaryDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.user, self.user_id = self.create_user("authuser", "authuser@example.com")

    @staticmethod
    def request_with_token(token: str) -> Request:
        return Request({
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/users/me",
            "raw_path": b"/users/me",
            "query_string": b"",
            "headers": [(b"authorization", f"Bearer {token}".encode("ascii"))],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        })

    def test_session_tokens_are_hashed_at_rest_and_legacy_tokens_upgrade(self):
        sessions = SessionFns(self.db)
        issued = sessions.issue(self.user_id)
        stored = sessions.db.get(issued.id)
        digest = hashlib.sha256(issued.token.encode("utf-8")).hexdigest()
        self.assertNotEqual(stored.token, issued.token)
        self.assertEqual(stored.token, digest)
        self.assertEqual(sessions.read_by_token(issued.token).id, issued.id)

        legacy_token = "legacy-plaintext-token"
        legacy_id = sessions.db.insert(Session(
            token=legacy_token,
            user_id=self.user_id,
            expires_at=datetime.datetime.now() + datetime.timedelta(days=1),
        ))
        self.assertEqual(sessions.read_by_token(legacy_token).id, legacy_id)
        legacy_stored = sessions.db.get(legacy_id)
        self.assertEqual(
            legacy_stored.token,
            hashlib.sha256(legacy_token.encode("utf-8")).hexdigest(),
        )

    def test_startup_migration_hashes_legacy_session_tokens(self):
        sessions = SessionFns(self.db)
        legacy_token = "legacy-session-to-migrate"
        session_id = sessions.db.insert(Session(
            token=legacy_token,
            user_id=self.user_id,
            expires_at=datetime.datetime.now() + datetime.timedelta(days=1),
        ))

        self.assertEqual(sessions.migrate_plaintext_tokens(), 1)
        stored = sessions.db.get(session_id)
        self.assertEqual(
            stored.token,
            hashlib.sha256(legacy_token.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(sessions.migrate_plaintext_tokens(), 0)

    def test_auth_rejects_expired_and_revoked_sessions(self):
        sessions = SessionFns(self.db)
        expired = sessions.issue(self.user_id)
        revoked = sessions.issue(self.user_id)
        sessions.db.query().where(id=expired.id).update(
            expires_at=datetime.datetime.now() - datetime.timedelta(seconds=1),
        )
        sessions.revoke(revoked.id)

        with patch("backend.sqliteback.Helpers.AuthHelp.DB", self.db):
            with self.assertRaises(HTTPException) as expired_error:
                get_current_user(self.request_with_token(expired.token))
            self.assertEqual(expired_error.exception.status_code, 401)
            with self.assertRaises(HTTPException) as revoked_error:
                get_current_user(self.request_with_token(revoked.token))
            self.assertEqual(revoked_error.exception.status_code, 401)

    def test_password_change_revokes_other_sessions(self):
        sessions = SessionFns(self.db)
        current = sessions.issue(self.user_id)
        other = sessions.issue(self.user_id)
        UserFns(self.db).change_password(
            self.user_id,
            "Secret123!",
            "NewSecret456!",
            preserve_session_id=current.id,
        )
        self.assertFalse(sessions.read(current.id).revoked)
        self.assertTrue(sessions.read(other.id).revoked)

    def test_cors_requires_explicit_http_origins(self):
        self.assertEqual(
            parse_cors_origins("https://example.test, http://localhost:5173/"),
            ["https://example.test", "http://localhost:5173"],
        )
        with self.assertRaises(ValueError):
            parse_cors_origins("*")
        with self.assertRaises(ValueError):
            parse_cors_origins("https://example.test/path")

    def test_api_responses_include_security_headers(self):
        response = TestClient(app).get("/health")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cache-control"], "no-store")


class IdentityFlowTests(TemporaryDatabaseTestCase):

    def test_notification_workflow_and_authenticated_api(self):
        actor, actor_id = self.create_user("notifier", "notifier@example.com")
        recipient, recipient_id = self.create_user("recipient", "recipient@example.com")
        notifications = NotificationFns(self.db)

        notification_id = notifications.notify(
            recipient_id,
            "comment",
            "notifier commented on your post.",
            actor_user_id=actor_id,
            target_type="post",
            target_id=24,
        )
        self.assertIsNotNone(notification_id)
        self.assertIsNone(
            notifications.notify(
                recipient_id,
                "comment",
                "self event",
                actor_user_id=recipient_id,
            )
        )
        self.assertEqual(notifications.unread_count(recipient_id), 1)

        previous_fns = NotificationRts.notification_fns
        previous_overrides = dict(app.dependency_overrides)
        NotificationRts.notification_fns = notifications
        app.dependency_overrides[get_current_user] = lambda: recipient
        client = TestClient(app)
        try:
            response = client.get("/notifications/")
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["unread_count"], 1)
            self.assertEqual(data["notifications"][0]["actor_username"], actor.username)
            self.assertEqual(data["notifications"][0]["target_id"], 24)

            response = client.patch(f"/notifications/{notification_id}/read")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(notifications.unread_count(recipient_id), 0)

            response = client.post("/notifications/read-all")
            self.assertEqual(response.status_code, 200)
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            NotificationRts.notification_fns = previous_fns

    def test_signup_creates_profile_for_account(self):
        user, user_id = self.create_user("alice", "alice@example.com")
        profile = self.db.use("profiles").query().where(user_id=user_id).first()
        self.assertIsNotNone(profile)
        if profile is None:
            self.fail("Signup did not create a profile.")
        self.assertEqual(profile["user_id"], user_id)

    def test_login_rejects_any_invalid_identity_with_generic_result(self):
        self.create_user("bob", "bob@example.com")
        self.assertIsNone(SessionFns(self.db).login(username="bob", password="wrongpass"))
        self.assertIsNone(SessionFns(self.db).login(username="missing", password="Secret123!"))

    def test_profile_can_be_read_by_username(self):
        _, user_id = self.create_user("carol", "carol@example.com", display_name="Carol")
        self.db.use("profiles").query().where(user_id=user_id).update(phone="555-0100")

        profile = ProfileFns(self.db).read_by_username("carol")
        self.assertIsNotNone(profile)
        if profile is None:
            self.fail("Profile lookup returned no profile.")
        self.assertEqual(profile["username"], "carol")
        self.assertEqual(profile["display_name"], "Carol")
        self.assertIsNone(profile["email"])
        owner_profile = ProfileFns(self.db).read_by_username("carol", viewer_user_id=user_id)
        self.assertIsNotNone(owner_profile)
        if owner_profile is None:
            self.fail("Owner profile lookup returned no profile.")
        self.assertEqual(owner_profile["email"], "carol@example.com")
        self.assertEqual(owner_profile["phone"], "555-0100")

    def test_database_creation_preserves_rows_across_reopen(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "persistent.sqlite"
            first_db = Database(database_path)
            users = Table(User, name="users")
            first_db.create(users)
            first_db.create(users)
            users.insert(
                User(
                    username="persisted",
                    email="persisted@example.com",
                    password_hash="hash",
                )
            )
            first_db.close()

            second_db = Database(database_path)
            second_users = Table(User, name="users")
            second_db.create(second_users)
            persisted = second_users.query().where(username="persisted").first()
            self.assertIsNotNone(persisted)
            if persisted is None:
                self.fail("Persisted row was not found after reopen.")
            self.assertEqual(persisted["email"], "persisted@example.com")
            second_db.close()

    def test_legacy_reactions_migrate_to_profile_chips(self):
        _, user_id = self.create_user("legacy", "legacy@example.com")
        profile = self.db.use("profiles").query().where(user_id=user_id).first()
        self.assertIsNotNone(profile)
        if profile is None:
            self.fail("User profile was not created.")

        self.db._execute(
            "CREATE TABLE reactions (id INTEGER PRIMARY KEY, post_id INTEGER, "
            "reacted_by INTEGER, reaction TEXT, created_at TEXT)"
        )
        self.db._execute(
            "INSERT INTO reactions (id, post_id, reacted_by, reaction, created_at) "
            "VALUES (1, 50, ?, '🔥', '2026-10-14T12:00:00')",
            [user_id],
        )
        self.db._conn.commit()

        migrate_reactions_to_chips(self.db)

        chip = self.db.use("chips").query().where(
            chipped_to=50,
            chipped_by=profile.id,
            kind="reaction",
        ).first()
        self.assertIsNotNone(chip)
        self.assertFalse(self.db.exists("reactions"))


class PostFeatureTests(TemporaryDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.author, self.author_id = self.create_user("postauthor", "postauthor@example.com")
        self.other_user, self.other_user_id = self.create_user("replyauthor", "replyauthor@example.com")
        self.posts = PostFns(self.db)

    def test_dashboard_analytics_aggregates_activity_and_dated_chips(self):
        root = self.posts.create(self.author_id, "Analytics post")
        self.posts.create_comment(self.author_id, root["id"], "Analytics comment")
        self.posts.toggle_reaction(root["id"], self.other_user_id, "🔥")
        AnalyticsFns(self.db)

        profiles = ProfileFns(self.db)
        _, third_user_id = self.create_user("third", "third@example.com")
        profiles.set_profile_chip(self.other_user_id, self.author_id, "follow", True)
        profiles.set_profile_chip(third_user_id, self.author_id, "star", True)
        target_profile = self.db.use("profiles").query().where(user_id=self.author_id).first()
        start = datetime.datetime.now().date() - datetime.timedelta(days=6)
        self.db.use("chips").query().where(
            chipped_to=target_profile.id,
            chipped_by=self.db.use("profiles").query().where(user_id=self.other_user_id).first().id,
            kind="follow",
        ).update(created_at=datetime.datetime.combine(start + datetime.timedelta(days=2), datetime.time.min))
        self.db.use("chips").query().where(
            chipped_to=target_profile.id,
            chipped_by=self.db.use("profiles").query().where(user_id=third_user_id).first().id,
            kind="star",
        ).update(created_at=datetime.datetime.combine(start + datetime.timedelta(days=4), datetime.time.min))

        report = AnalyticsFns(self.db).dashboard(self.author_id, days=7)
        self.assertEqual(report["total_posts"], 1)
        self.assertEqual(report["total_comments"], 1)
        self.assertEqual(report["total_reactions"], 1)
        self.assertEqual(report["dominant_reaction"], "🔥")
        self.assertEqual(len(report["time_series"]), 7)
        self.assertEqual(report["time_series"][1]["followers"], 0)
        self.assertEqual(report["time_series"][2]["followers"], 1)
        self.assertEqual(report["time_series"][4]["stars"], 1)

        previous_fns = AnalyticsRts.analytics_fns
        previous_overrides = dict(app.dependency_overrides)
        AnalyticsRts.analytics_fns = AnalyticsFns(self.db)
        app.dependency_overrides[get_current_user] = lambda: self.author
        client = TestClient(app)
        try:
            response = client.get("/analytics/me?days=7")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["total_posts"], 1)
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            AnalyticsRts.analytics_fns = previous_fns

    def test_post_interactions_create_notifications_only_on_new_events(self):
        root = self.posts.create(self.author_id, "Notify me")
        self.posts.create_comment(self.other_user_id, root["id"], "A real comment")
        self.posts.toggle_reaction(root["id"], self.other_user_id, "🔥")
        self.posts.toggle_reaction(root["id"], self.other_user_id, "🔥")

        notifications = NotificationFns(self.db).list_for_user(self.author_id)
        self.assertEqual([item["kind"] for item in notifications], ["reaction", "comment"])
        self.assertEqual(NotificationFns(self.db).unread_count(self.author_id), 2)

    def test_follow_and_star_chips_are_unique_and_listed(self):
        target, target_id = self.create_user("target", "target@example.com")
        profiles = ProfileFns(self.db)

        followed = profiles.set_profile_chip(self.author_id, target_id, "follow", True)
        profiles.set_profile_chip(self.author_id, target_id, "follow", True)
        starred = profiles.set_profile_chip(self.author_id, target_id, "star", True)
        profiles.set_profile_chip(self.author_id, target_id, "star", True)

        self.assertTrue(followed["followed_by_me"])
        self.assertTrue(starred["starred_by_me"])
        self.assertEqual(starred["followers"], 1)
        self.assertEqual(starred["stars"], 1)
        self.assertEqual(NotificationFns(self.db).unread_count(target_id), 2)
        self.assertEqual(len(profiles.list_connections(target_id, self.author_id, "followers")), 1)

        actor_profile = self.db.use("profiles").query().where(user_id=self.author_id).first()
        target_profile = self.db.use("profiles").query().where(user_id=target_id).first()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.use("chips").insert(
                Chip(
                    chipped_by=actor_profile.id,
                    chipped_to=target_profile.id,
                    kind="follow",
                    content="",
                )
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db._execute(
                "INSERT INTO chips (chipped_by, chipped_to, kind, content) "
                "VALUES (?, ?, 'invalid', '')",
                [actor_profile.id, target_profile.id],
            )

        previous_fns = ProfileRts.profile_fns
        previous_overrides = dict(app.dependency_overrides)
        ProfileRts.profile_fns = profiles
        app.dependency_overrides[get_current_user] = lambda: self.author
        client = TestClient(app)
        try:
            response = client.get(f"/profiles/{target_id}/followers")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["profiles"][0]["username"], self.author.username)

            response = client.get(f"/profiles/by-username/{target.username}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["data"]["profile"]["followed_by_me"])
            self.assertTrue(response.json()["data"]["profile"]["starred_by_me"])

            response = client.post(
                f"/profiles/{target_id}/reactions",
                json={"reaction": "🔥"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["profile"]["reactions"], {"🔥": 1})
            self.assertEqual(response.json()["data"]["profile"]["my_reactions"], ["🔥"])

            response = client.post(
                f"/profiles/{target_id}/reactions",
                json={"reaction": "🔥"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["profile"]["reactions"], {})

            response = client.delete(f"/profiles/{target_id}/follow")
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["data"]["profile"]["followed_by_me"])
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            ProfileRts.profile_fns = previous_fns

    def test_profile_reaction_does_not_collide_with_post_id(self):
        root = self.posts.create(self.author_id, "Same numeric profile/post ID")
        author_profile = self.db.use("profiles").query().where(user_id=self.author_id).first()
        self.assertEqual(root["id"], author_profile.id)

        profiles = ProfileFns(self.db)
        profiles.toggle_profile_reaction(self.other_user_id, self.author_id, "❤️")
        self.posts.toggle_reaction(root["id"], self.other_user_id, "🔥")

        post = self.posts.read(root["id"], self.other_user_id)
        profile = profiles.read_for_user(self.author_id, viewer_user_id=self.other_user_id)
        self.assertEqual(post["reactions"], {"🔥": 1})
        self.assertEqual(profile["reactions"], {"❤️": 1})

        self.assertTrue(self.posts.delete(root["id"], self.author_id))
        remaining_profile = profiles.read_for_user(
            self.author_id,
            viewer_user_id=self.other_user_id,
        )
        self.assertEqual(remaining_profile["reactions"], {"❤️": 1})

    def test_reply_to_is_independent_from_comment_flag_and_comments_thread(self):
        root = self.posts.create(self.author_id, "Root post")
        reply = self.posts.create(
            self.other_user_id,
            "A reply that is not a comment",
            reply_to=root["id"],
            is_comment=False,
        )
        comment = self.posts.create_comment(
            self.author_id,
            root["id"],
            "A nested comment",
            reply_to=reply["id"],
        )
        comment_reply = self.posts.create_comment(
            self.other_user_id,
            root["id"],
            "A reply to the nested comment",
            reply_to=comment["id"],
        )
        unattached_comment = self.posts.create(
            self.author_id,
            "An explicit comment without a reply target",
            is_comment=True,
        )

        self.assertFalse(reply["is_comment"])
        self.assertEqual(reply["reply_to"], root["id"])
        self.assertEqual(root["root_post_id"], root["id"])
        self.assertEqual(reply["root_post_id"], root["id"])
        self.assertTrue(comment["is_comment"])
        self.assertEqual(comment["reply_to"], reply["id"])
        self.assertEqual(comment["root_post_id"], root["id"])
        self.assertTrue(unattached_comment["is_comment"])
        self.assertIsNone(unattached_comment["reply_to"])
        self.assertEqual(unattached_comment["root_post_id"], unattached_comment["id"])
        refreshed_root = self.posts.read(root["id"], self.author_id)
        self.assertIsNotNone(refreshed_root)
        if refreshed_root is None:
            self.fail("Root post was not found.")
        self.assertEqual(refreshed_root["comments"], 2)
        comments = self.posts.comments_for(root["id"], self.author_id)
        self.assertEqual({item["id"] for item in comments}, {comment["id"], comment_reply["id"]})
        self.assertEqual(comments[0]["root_post_id"], root["id"])
        replies = self.posts.comments_for(comment["id"], self.author_id)
        self.assertEqual([item["id"] for item in replies], [comment_reply["id"]])
        self.assertEqual(replies[0]["root_post_id"], root["id"])

    def test_reactions_toggle_per_user_and_delete_removes_thread(self):
        root = self.posts.create(self.author_id, "Root post")
        comment = self.posts.create_comment(
            self.other_user_id,
            root["id"],
            "A comment",
        )

        reacted = self.posts.toggle_reaction(root["id"], self.other_user_id, "👍")
        self.assertIsNotNone(reacted)
        if reacted is None:
            self.fail("Reaction response was empty.")
        self.assertEqual(reacted["reactions"], {"👍": 1})
        self.assertEqual(reacted["my_reactions"], ["👍"])
        unreacted = self.posts.toggle_reaction(root["id"], self.other_user_id, "👍")
        self.assertIsNotNone(unreacted)
        if unreacted is None:
            self.fail("Reaction removal response was empty.")
        self.assertEqual(unreacted["reactions"], {})

        with self.assertRaises(PermissionError):
            self.posts.delete(root["id"], self.other_user_id)

        self.assertTrue(self.posts.delete(root["id"], self.author_id))
        self.assertIsNone(self.posts.read(comment["id"], self.author_id))

    def test_post_list_batches_profile_state_and_reads(self):
        self.posts.create(self.author_id, "First author post")
        self.posts.create(self.author_id, "Second author post")
        self.posts.create(self.other_user_id, "Another author post")

        with patch.object(
            self.posts.profile_chips,
            "profile_states",
            wraps=self.posts.profile_chips.profile_states,
        ) as profile_states:
            with patch.object(self.db, "_execute", wraps=self.db._execute) as execute:
                self.posts.list_all(self.author_id)
                initial_query_count = execute.call_count

        self.assertEqual(profile_states.call_count, 1)
        self.assertEqual(profile_states.call_args.args[1], {self.author_id, self.other_user_id})

        for index in range(5):
            self.posts.create(self.author_id, f"Additional author post {index}")

        with patch.object(self.db, "_execute", wraps=self.db._execute) as execute:
            self.posts.list_all(self.author_id)
        self.assertEqual(execute.call_count, initial_query_count)

    def test_post_http_workflow(self):
        previous_fns = PostRts.post_fns
        previous_overrides = dict(app.dependency_overrides)
        PostRts.post_fns = self.posts
        app.dependency_overrides[get_current_user] = lambda: self.author
        client = TestClient(app)
        try:
            created = client.post("/posts/", json={"content": "HTTP post"})
            self.assertEqual(created.status_code, 201)
            post_id = created.json()["data"]["post"]["id"]

            comment = client.post(
                f"/posts/{post_id}/comments",
                json={"content": "HTTP comment"},
            )
            self.assertEqual(comment.status_code, 201)
            self.assertTrue(comment.json()["data"]["post"]["is_comment"])

            reaction = client.post(
                f"/posts/{post_id}/reactions",
                json={"reaction": "🔥"},
            )
            self.assertEqual(reaction.status_code, 200)
            self.assertEqual(reaction.json()["data"]["post"]["reactions"], {"🔥": 1})

            updated = client.patch(
                f"/posts/{post_id}",
                json={"content": "Edited HTTP post"},
            )
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json()["data"]["post"]["content"], "Edited HTTP post")

            comments = client.get(f"/posts/{post_id}/comments")
            self.assertEqual(comments.status_code, 200)
            self.assertEqual(len(comments.json()["data"]["comments"]), 1)

            my_posts = client.get("/posts/me")
            self.assertEqual(my_posts.status_code, 200)
            self.assertEqual(len(my_posts.json()["data"]["posts"]), 2)

            deleted = client.delete(f"/posts/{post_id}")
            self.assertEqual(deleted.status_code, 200)
            self.assertEqual(client.get(f"/posts/{post_id}").status_code, 404)
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            PostRts.post_fns = previous_fns

    def test_feed_endpoint_returns_real_posts_and_profile_details(self):
        root = self.posts.create(self.author_id, "Feed root")
        reply = self.posts.create(
            self.other_user_id,
            "Ordinary reply",
            reply_to=root["id"],
            is_comment=False,
        )
        comment = self.posts.create_comment(self.author_id, root["id"], "Thread comment")

        previous_fns = FeedRts.feed_fns
        previous_overrides = dict(app.dependency_overrides)
        FeedRts.feed_fns = FeedFns(self.db)
        app.dependency_overrides[get_optional_current_user] = lambda: self.author
        client = TestClient(app)
        try:
            response = client.get("/feed/")
            self.assertEqual(response.status_code, 200)
            posts = response.json()["data"]["posts"]
            ids = [post["id"] for post in posts]
            self.assertIn(root["id"], ids)
            self.assertIn(reply["id"], ids)
            self.assertNotIn(comment["id"], ids)

            own_post = next(post for post in posts if post["id"] == root["id"])
            other_post = next(post for post in posts if post["id"] == reply["id"])
            self.assertEqual(own_post["profile"]["username"], "postauthor")
            self.assertEqual(own_post["profile"]["email"], "postauthor@example.com")
            self.assertIsNone(other_post["profile"]["email"])
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            FeedRts.feed_fns = previous_fns

    def test_feed_and_threads_are_public_but_mutations_require_auth(self):
        root = self.posts.create(self.author_id, "Public thread")
        comment = self.posts.create_comment(self.other_user_id, root["id"], "Public reply")
        previous_feed_fns = FeedRts.feed_fns
        previous_post_fns = PostRts.post_fns
        FeedRts.feed_fns = FeedFns(self.db)
        PostRts.post_fns = self.posts
        client = TestClient(app)
        try:
            self.assertEqual(client.get("/feed/").status_code, 200)
            self.assertEqual(client.get("/posts/").status_code, 200)

            post_response = client.get(f"/posts/{root['id']}")
            self.assertEqual(post_response.status_code, 200)
            guest_post = post_response.json()["data"]["post"]
            self.assertIsNone(guest_post["profile"]["email"])
            self.assertEqual(guest_post["my_reactions"], [])

            comments_response = client.get(f"/posts/{root['id']}/comments")
            self.assertEqual(comments_response.status_code, 200)
            self.assertEqual(
                [item["id"] for item in comments_response.json()["data"]["comments"]],
                [comment["id"]],
            )
            self.assertEqual(
                client.post("/posts/", json={"content": "Must sign in"}).status_code,
                401,
            )
        finally:
            FeedRts.feed_fns = previous_feed_fns
            PostRts.post_fns = previous_post_fns

    def test_feed_cursor_pages_are_ordered_unique_and_exclude_comments(self):
        roots = [self.posts.create(self.author_id, f"Page post {index}") for index in range(5)]
        self.posts.create_comment(self.other_user_id, roots[-1]["id"], "Not a feed root")

        first_page, cursor = self.posts.feed_page(limit=2)
        second_page, next_cursor = self.posts.feed_page(limit=2, before_id=cursor)
        third_page, final_cursor = self.posts.feed_page(limit=2, before_id=next_cursor)

        page_ids = [post["id"] for post in first_page + second_page + third_page]
        self.assertEqual(page_ids, sorted(page_ids, reverse=True))
        self.assertEqual(len(page_ids), len(set(page_ids)))
        self.assertTrue(all(not post["is_comment"] for post in first_page + second_page + third_page))
        self.assertIsNotNone(cursor)
        self.assertIsNotNone(next_cursor)
        self.assertIsNone(final_cursor)


if __name__ == "__main__":
    unittest.main()
