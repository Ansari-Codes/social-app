"""
Functions/PostFns.py — post, comment, and reaction domain operations.
"""

import datetime
import threading
import time
from collections import defaultdict
from typing import Optional

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import Chip, DB, Post, Profile, User
from backend.sqliteback.Functions.AnalyticsFns import invalidate_analytics_cache
from backend.sqliteback.Functions.ChipFns import ChipFns
from backend.sqliteback.Functions.NotificationFns import NotificationFns

_POSTS_CACHE = None
_POSTS_CACHE_TIME = 0.0
_POSTS_CACHE_LOCK = threading.Lock()
_POSTS_CACHE_TTL = 10.0


def invalidate_posts_cache() -> None:
    global _POSTS_CACHE, _POSTS_CACHE_TIME
    with _POSTS_CACHE_LOCK:
        _POSTS_CACHE = None
        _POSTS_CACHE_TIME = 0.0


class PostFns:
    def __init__(self, db: Database = DB):
        self.posts = db.use("posts")
        self.users = db.use("users")
        self.profiles = db.use("profiles")
        self.chips = db.use("chips")
        self.profile_chips = ChipFns(db)
        self.notifications = NotificationFns(db)

    def _profile_id(self, user_id: int) -> int:
        row = self.profiles.query().where(user_id=user_id).first()
        if row is None:
            raise LookupError("Profile not found for user.")
        return row.id

    def _post(self, post_id: int) -> Optional[Post]:
        row = self.posts.get(post_id)
        return row.to_model() if row is not None else None

    def _context(self):
        global _POSTS_CACHE, _POSTS_CACHE_TIME
        now = time.monotonic()
        with _POSTS_CACHE_LOCK:
            if _POSTS_CACHE is not None and now - _POSTS_CACHE_TIME < _POSTS_CACHE_TTL:
                return _POSTS_CACHE

        rows = [row.to_model() for row in self.posts.query().all()]
        by_id = {row.id: row for row in rows}
        reaction_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        reaction_owners: dict[int, set[tuple[int, str]]] = defaultdict(set)
        for row in self.chips.query().where(kind="reaction").all():
            if row.content.startswith("profile:"):
                continue
            reaction_counts[row.chipped_to][row.content] += 1
            reaction_owners[row.chipped_to].add((row.chipped_by, row.content))

        comment_counts: dict[int, int] = defaultdict(int)
        for comment in rows:
            if not comment.is_comment or comment.reply_to is None:
                continue
            parent_id = comment.reply_to
            visited: set[int] = set()
            while parent_id is not None and parent_id not in visited:
                visited.add(parent_id)
                comment_counts[parent_id] += 1
                parent = by_id.get(parent_id)
                if parent is None:
                    break
                parent_id = parent.reply_to

        result = (rows, by_id, reaction_counts, reaction_owners, comment_counts)
        with _POSTS_CACHE_LOCK:
            _POSTS_CACHE = result
            _POSTS_CACHE_TIME = now
        return result

    @staticmethod
    def _root_post_id(post: Post, by_id: dict[int, Post]) -> int:
        current = post
        visited: set[int] = set()
        while current.reply_to is not None and current.id not in visited:
            visited.add(current.id)
            parent = by_id.get(current.reply_to)
            if parent is None:
                break
            current = parent
        return current.id

    def _serialize(
        self,
        post: Post,
        viewer_user_id: Optional[int],
        by_id: dict[int, Post],
        reaction_counts: dict[int, dict[str, int]],
        reaction_owners: dict[int, set[tuple[int, str]]],
        comment_counts: dict[int, int],
        profile_state_cache: Optional[dict[int, dict]] = None,
        user_cache: Optional[dict[int, User]] = None,
        profile_cache: Optional[dict[int, Profile]] = None,
        prefetched_viewer_profile_id: Optional[int] = None,
    ) -> dict:
        if user_cache is None:
            user_row = self.users.get(post.user_id)
            if user_row is None:
                raise LookupError("Post author not found.")
            user: User = user_row.to_model()
        else:
            user = user_cache.get(post.user_id)
            if user is None:
                raise LookupError("Post author not found.")

        if profile_cache is None:
            profile_row = self.profiles.query().where(user_id=post.user_id).first()
            profile: Optional[Profile] = profile_row.to_model() if profile_row else None
        else:
            profile = profile_cache.get(post.user_id)

        viewer_profile_id = prefetched_viewer_profile_id
        if viewer_profile_id is None and viewer_user_id is not None:
            viewer_profile_id = self._profile_id(viewer_user_id)
        if profile_state_cache is None:
            profile_state = self.profile_chips.profile_state(viewer_user_id, post.user_id)
        else:
            if post.user_id not in profile_state_cache:
                profile_state_cache[post.user_id] = self.profile_chips.profile_state(
                    viewer_user_id,
                    post.user_id,
                )
            profile_state = profile_state_cache[post.user_id]

        reply_to_author = None
        reply_to_snippet = None
        if post.reply_to is not None and post.reply_to in by_id:
            parent_post = by_id[post.reply_to]
            if user_cache is None:
                parent_user_row = self.users.get(parent_post.user_id)
                parent_user = parent_user_row.to_model() if parent_user_row else None
            else:
                parent_user = user_cache.get(parent_post.user_id)
            if parent_user is not None:
                reply_to_author = parent_user.display_name or parent_user.username
            clean_parent = " ".join(parent_post.content.split())
            reply_to_snippet = clean_parent[:80] + ("..." if len(clean_parent) > 80 else "")

        return {
            "id": post.id,
            "root_post_id": self._root_post_id(post, by_id),
            "user_id": post.user_id,
            "profile": {
                "id": profile.id if profile else user.id,
                "user_id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "emoji": profile.emoji if profile else None,
                "about": profile.about if profile else None,
                "powerline": profile.powerline if profile else None,
                "banner_color": profile.banner_color if profile else None,
                "birthday": profile.birthday if profile else None,
                "phone": profile.phone if profile and user.id == viewer_user_id else None,
                "email": user.email if user.id == viewer_user_id else None,
                **profile_state,
            },
            "content": post.content,
            "reply_to": post.reply_to,
            "reply_to_author": reply_to_author,
            "reply_to_snippet": reply_to_snippet,
            "is_comment": post.is_comment,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "reactions": dict(reaction_counts.get(post.id, {})),
            "my_reactions": sorted(
                reaction
                for profile_id, reaction in reaction_owners.get(post.id, set())
                if profile_id == viewer_profile_id
            ),
            "comments": comment_counts.get(post.id, 0),
        }

    def _payload(self, post: Post, viewer_user_id: Optional[int]) -> dict:
        _, by_id, reaction_counts, reaction_owners, comment_counts = self._context()
        return self._serialize(
            post,
            viewer_user_id,
            by_id,
            reaction_counts,
            reaction_owners,
            comment_counts,
        )

    def _thread_comment_count(self, post_id: int) -> int:
        row = self.posts._db._execute(
            """
            WITH RECURSIVE descendants(id) AS (
                SELECT id FROM posts WHERE reply_to = ?
                UNION
                SELECT child.id
                FROM posts AS child
                JOIN descendants AS parent ON child.reply_to = parent.id
            )
            SELECT COUNT(*) AS count
            FROM descendants
            JOIN posts AS comment ON comment.id = descendants.id
            WHERE comment.is_comment = 1
            """,
            [post_id],
        ).fetchone()
        return int(row["count"]) if row is not None else 0

    def _single_payload(self, post: Post, viewer_user_id: Optional[int]) -> dict:
        user_row = self.users.get(post.user_id)
        if user_row is None:
            raise LookupError("Post author not found.")
        user: User = user_row.to_model()

        profile_row = self.profiles.query().where(user_id=post.user_id).first()
        profile: Optional[Profile] = profile_row.to_model() if profile_row else None

        viewer_profile_id = None
        if viewer_user_id is not None:
            viewer_profile_row = self.profiles.query().where(user_id=viewer_user_id).first()
            viewer_profile_id = (
                viewer_profile_row.id if viewer_profile_row else self._profile_id(viewer_user_id)
            )

        profile_state = self.profile_chips.profile_state(
            viewer_user_id,
            post.user_id,
            profiles_by_user_id={post.user_id: profile} if profile else None,
        )

        reply_to_author = None
        reply_to_snippet = None
        root_post_id = post.id
        if post.reply_to is not None:
            parent_row = self.posts.get(post.reply_to)
            if parent_row is not None:
                parent_post = parent_row.to_model()
                parent_user_row = self.users.get(parent_post.user_id)
                if parent_user_row is not None:
                    parent_user = parent_user_row.to_model()
                    reply_to_author = parent_user.display_name or parent_user.username
                clean_parent = " ".join(parent_post.content.split())
                reply_to_snippet = clean_parent[:80] + ("..." if len(clean_parent) > 80 else "")

                curr = parent_post
                visited = {post.id}
                while curr.reply_to is not None and curr.id not in visited:
                    visited.add(curr.id)
                    next_parent_row = self.posts.get(curr.reply_to)
                    if next_parent_row is None:
                        break
                    curr = next_parent_row.to_model()
                root_post_id = curr.id

        reaction_rows = self.chips.query().where(chipped_to=post.id, kind="reaction").all()
        reaction_counts: dict[str, int] = defaultdict(int)
        my_reactions = []
        for r_row in reaction_rows:
            chip = r_row.to_model()
            if chip.content.startswith("profile:"):
                continue
            reaction_counts[chip.content] += 1
            if chip.chipped_by == viewer_profile_id:
                my_reactions.append(chip.content)

        comment_count = self._thread_comment_count(post.id)

        return {
            "id": post.id,
            "root_post_id": root_post_id,
            "user_id": post.user_id,
            "profile": {
                "id": profile.id if profile else user.id,
                "user_id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "emoji": profile.emoji if profile else None,
                "about": profile.about if profile else None,
                "powerline": profile.powerline if profile else None,
                "banner_color": profile.banner_color if profile else None,
                "birthday": profile.birthday if profile else None,
                "phone": profile.phone if profile and user.id == viewer_user_id else None,
                "email": user.email if user.id == viewer_user_id else None,
                **profile_state,
            },
            "content": post.content,
            "reply_to": post.reply_to,
            "reply_to_author": reply_to_author,
            "reply_to_snippet": reply_to_snippet,
            "is_comment": post.is_comment,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "reactions": dict(reaction_counts),
            "my_reactions": sorted(my_reactions),
            "comments": comment_count,
        }

    def _serialize_many(
        self,
        posts: list[Post],
        viewer_user_id: Optional[int],
        by_id: dict[int, Post],
        reaction_counts: dict[int, dict[str, int]],
        reaction_owners: dict[int, set[tuple[int, str]]],
        comment_counts: dict[int, int],
    ) -> list[dict]:
        author_ids = {post.user_id for post in posts}
        related_user_ids = author_ids | (
            {viewer_user_id} if viewer_user_id is not None else set()
        )
        for post in posts:
            parent = by_id.get(post.reply_to) if post.reply_to is not None else None
            if parent is not None:
                related_user_ids.add(parent.user_id)

        users = {
            row.id: row.to_model()
            for row in self.users.query().where(id=list(related_user_ids)).all()
        }
        profiles = {
            row.user_id: row.to_model()
            for row in self.profiles.query().where(user_id=list(related_user_ids)).all()
        }
        profile_states = self.profile_chips.profile_states(
            viewer_user_id,
            author_ids,
            profiles,
        )
        viewer_profile = profiles.get(viewer_user_id) if viewer_user_id is not None else None
        viewer_profile_id = (
            viewer_profile.id
            if viewer_profile is not None
            else self._profile_id(viewer_user_id) if viewer_user_id is not None else None
        )

        return [
            self._serialize(
                post,
                viewer_user_id,
                by_id,
                reaction_counts,
                reaction_owners,
                comment_counts,
                profile_states,
                users,
                profiles,
                viewer_profile_id,
            )
            for post in posts
        ]

    def _validate_content(self, content: str) -> str:
        normalized = content.strip()
        if not normalized:
            raise ValueError("Post content cannot be empty.")
        if len(normalized) > 10000:
            raise ValueError("Post content cannot exceed 10000 characters.")
        return normalized

    def _validate_parent(self, parent_id: Optional[int], post_id: Optional[int] = None) -> None:
        if parent_id is None:
            return
        if parent_id == post_id:
            raise ValueError("A post cannot reply to itself.")
        if self.posts.get(parent_id) is None:
            raise LookupError("Reply target not found.")

    def _belongs_to_thread(self, candidate_id: int, root_id: int) -> bool:
        current = self._post(candidate_id)
        visited: set[int] = set()
        while current is not None and current.id not in visited:
            if current.id == root_id:
                return True
            visited.add(current.id)
            if current.reply_to is None:
                return False
            current = self._post(current.reply_to)
        return False

    def list_all(self, viewer_user_id: Optional[int] = None) -> list[dict]:
        rows, by_id, reaction_counts, reaction_owners, comment_counts = self._context()
        rows.sort(key=lambda post: post.created_at, reverse=True)
        return self._serialize_many(
            rows,
            viewer_user_id,
            by_id,
            reaction_counts,
            reaction_owners,
            comment_counts,
        )

    def feed(self, viewer_user_id: Optional[int] = None) -> list[dict]:
        rows, by_id, reaction_counts, reaction_owners, comment_counts = self._context()
        feed_rows = [post for post in rows if not post.is_comment]
        feed_rows.sort(key=lambda post: post.created_at, reverse=True)
        return self._serialize_many(
            feed_rows,
            viewer_user_id,
            by_id,
            reaction_counts,
            reaction_owners,
            comment_counts,
        )

    def feed_page(
        self,
        viewer_user_id: Optional[int] = None,
        *,
        limit: int = 20,
        before_id: Optional[int] = None,
    ) -> tuple[list[dict], Optional[int]]:
        limit = max(1, min(limit, 50))
        query = self.posts.query().where(is_comment=False)
        if before_id is not None:
            query = query.where_lt("id", before_id)
        rows = [
            row.to_model()
            for row in query.order_by("id", desc=True).limit(limit + 1).all()
        ]
        has_more = len(rows) > limit
        page = rows[:limit]
        if not page:
            return [], None

        post_ids = [post.id for post in page if post.id is not None]
        placeholders = ",".join("?" for _ in post_ids)
        context_sql = f"""
            WITH RECURSIVE ancestors(id, user_id, content, reply_to, is_comment, created_at, updated_at) AS (
                SELECT id, user_id, content, reply_to, is_comment, created_at, updated_at
                FROM posts WHERE id IN ({placeholders})
                UNION
                SELECT parent.id, parent.user_id, parent.content, parent.reply_to,
                       parent.is_comment, parent.created_at, parent.updated_at
                FROM posts AS parent
                JOIN ancestors AS child ON parent.id = child.reply_to
            )
            SELECT * FROM ancestors
        """
        context_rows = self.posts._db._execute(context_sql, post_ids).fetchall()
        by_id = {
            int(row["id"]): Post.model_validate(dict(row))
            for row in context_rows
        }

        reaction_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        reaction_owners: dict[int, set[tuple[int, str]]] = defaultdict(set)
        for row in self.chips.query().where(
            chipped_to=post_ids,
            kind="reaction",
        ).all():
            chip = row.to_model()
            if chip.content.startswith("profile:"):
                continue
            reaction_counts[chip.chipped_to][chip.content] += 1
            reaction_owners[chip.chipped_to].add((chip.chipped_by, chip.content))

        comment_sql = f"""
            WITH RECURSIVE descendants(root_id, post_id) AS (
                SELECT id, id FROM posts WHERE id IN ({placeholders})
                UNION
                SELECT descendants.root_id, child.id
                FROM posts AS child
                JOIN descendants ON child.reply_to = descendants.post_id
            )
            SELECT descendants.root_id, COUNT(*) AS count
            FROM descendants
            JOIN posts AS comment ON comment.id = descendants.post_id
            WHERE comment.is_comment = 1
              AND descendants.post_id <> descendants.root_id
            GROUP BY descendants.root_id
        """
        comment_counts = {
            int(row["root_id"]): int(row["count"])
            for row in self.posts._db._execute(comment_sql, post_ids).fetchall()
        }

        payload = self._serialize_many(
            page,
            viewer_user_id,
            by_id,
            reaction_counts,
            reaction_owners,
            comment_counts,
        )
        next_cursor = page[-1].id if has_more else None
        return payload, next_cursor

    def list_for_user(self, user_id: int, viewer_user_id: Optional[int] = None) -> list[dict]:
        rows, by_id, reaction_counts, reaction_owners, comment_counts = self._context()
        rows = [post for post in rows if post.user_id == user_id]
        rows.sort(key=lambda post: post.created_at, reverse=True)
        return self._serialize_many(
            rows,
            viewer_user_id,
            by_id,
            reaction_counts,
            reaction_owners,
            comment_counts,
        )

    def read(self, post_id: int, viewer_user_id: Optional[int] = None) -> Optional[dict]:
        post = self._post(post_id)
        if post is None:
            return None
        return self._single_payload(post, viewer_user_id)

    def create(
        self,
        user_id: int,
        content: str,
        *,
        reply_to: Optional[int] = None,
        is_comment: bool = False,
    ) -> dict:
        content = self._validate_content(content)
        self._validate_parent(reply_to)
        post = Post(
            user_id=user_id,
            content=content,
            reply_to=reply_to,
            is_comment=is_comment,
        )
        post_id = self.posts.insert(post)
        invalidate_posts_cache()
        invalidate_analytics_cache(user_id)
        created = self._post(post_id)
        if created is None:
            raise RuntimeError("Post creation failed unexpectedly.")
        if reply_to is not None and not is_comment:
            parent = self._post(reply_to)
            if parent is not None:
                self.notifications.notify(
                    parent.user_id,
                    "reply",
                    f"replied to your post #{parent.id}.",
                    actor_user_id=user_id,
                    target_type="post",
                    target_id=parent.id,
                )
        return self._single_payload(created, user_id)

    def create_comment(
        self,
        user_id: int,
        post_id: int,
        content: str,
        *,
        reply_to: Optional[int] = None,
    ) -> dict:
        if self._post(post_id) is None:
            raise LookupError("Post not found.")
        parent_id = post_id if reply_to is None else reply_to
        self._validate_parent(parent_id)
        if not self._belongs_to_thread(parent_id, post_id):
            raise ValueError("Comment reply target must belong to this post thread.")
        created = self.create(
            user_id,
            content,
            reply_to=parent_id,
            is_comment=True,
        )
        parent = self._post(parent_id)
        if parent is not None:
            target_type = "comment" if parent.is_comment else "post"
            self.notifications.notify(
                parent.user_id,
                "comment",
                "replied to your comment." if target_type == "comment" else "commented on your post.",
                actor_user_id=user_id,
                target_type=target_type,
                target_id=parent_id,
            )
        return created

    def comments_for(self, post_id: int, viewer_user_id: Optional[int] = None) -> list[dict]:
        root_post = self._post(post_id)
        if root_post is None:
            raise LookupError("Post not found.")

        descendants_sql = """
            WITH RECURSIVE descendants(id, user_id, content, reply_to, is_comment, created_at, updated_at) AS (
                SELECT id, user_id, content, reply_to, is_comment, created_at, updated_at
                FROM posts WHERE reply_to = ?
                UNION
                SELECT child.id, child.user_id, child.content, child.reply_to,
                       child.is_comment, child.created_at, child.updated_at
                FROM posts AS child
                JOIN descendants AS parent ON child.reply_to = parent.id
            )
            SELECT * FROM descendants
        """
        thread_posts = [
            Post.model_validate(dict(row))
            for row in self.posts._db._execute(descendants_sql, [post_id]).fetchall()
        ]
        if not thread_posts:
            return []
        descendants = [post for post in thread_posts if post.is_comment]

        ancestors_sql = """
            WITH RECURSIVE ancestors(id, user_id, content, reply_to, is_comment, created_at, updated_at) AS (
                SELECT id, user_id, content, reply_to, is_comment, created_at, updated_at
                FROM posts WHERE id = ?
                UNION
                SELECT parent.id, parent.user_id, parent.content, parent.reply_to,
                       parent.is_comment, parent.created_at, parent.updated_at
                FROM posts AS parent
                JOIN ancestors AS child ON parent.id = child.reply_to
            )
            SELECT * FROM ancestors
        """
        context_posts = {
            post.id: post
            for post in (
                Post.model_validate(dict(row))
                for row in self.posts._db._execute(ancestors_sql, [post_id]).fetchall()
            )
        }
        context_posts.update({post.id: post for post in thread_posts})
        by_id = context_posts
        descendant_ids = [post.id for post in descendants if post.id is not None]

        reaction_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        reaction_owners: dict[int, set[tuple[int, str]]] = defaultdict(set)
        for row in self.chips.query().where(
            chipped_to=descendant_ids,
            kind="reaction",
        ).all():
            chip = row.to_model()
            if chip.content.startswith("profile:"):
                continue
            reaction_counts[chip.chipped_to][chip.content] += 1
            reaction_owners[chip.chipped_to].add((chip.chipped_by, chip.content))

        comment_counts: dict[int, int] = defaultdict(int)
        for comment in descendants:
            if not comment.is_comment or comment.reply_to is None:
                continue
            parent_id = comment.reply_to
            visited: set[int] = set()
            while parent_id is not None and parent_id not in visited:
                visited.add(parent_id)
                comment_counts[parent_id] += 1
                parent = by_id.get(parent_id)
                if parent is None:
                    break
                parent_id = parent.reply_to

        descendants.sort(key=lambda post: post.created_at)
        return self._serialize_many(
            descendants,
            viewer_user_id,
            by_id,
            reaction_counts,
            reaction_owners,
            comment_counts,
        )

    def update(self, post_id: int, user_id: int, **fields) -> Optional[dict]:
        post = self._post(post_id)
        if post is None:
            return None
        if post.user_id != user_id:
            raise PermissionError("You can only edit your own posts.")

        changes = dict(fields)
        if "content" in changes:
            if changes["content"] is None:
                raise ValueError("Post content cannot be empty.")
            changes["content"] = self._validate_content(changes["content"])
        if "is_comment" in changes and changes["is_comment"] is None:
            raise ValueError("is_comment must be true or false.")
        if "reply_to" in changes:
            self._validate_parent(changes["reply_to"], post_id)
            if changes["reply_to"] is not None:
                parent_id = changes["reply_to"]
                visited: set[int] = set()
                while parent_id is not None and parent_id not in visited:
                    if parent_id == post_id:
                        raise ValueError("Reply update would create a post cycle.")
                    visited.add(parent_id)
                    parent = self._post(parent_id)
                    parent_id = parent.reply_to if parent else None
                if parent_id in visited:
                    raise ValueError("Reply target already belongs to a post cycle.")
        if not changes:
            return self.read(post_id, user_id)

        changes["updated_at"] = datetime.datetime.now()
        self.posts.query().where(id=post_id).update(**changes)
        invalidate_posts_cache()
        invalidate_analytics_cache(user_id)
        return self.read(post_id, user_id)

    def delete(self, post_id: int, user_id: int) -> bool:
        post = self._post(post_id)
        if post is None:
            return False
        if post.user_id != user_id:
            raise PermissionError("You can only delete your own posts.")

        descendants = self.posts._db._execute(
            """
            WITH RECURSIVE descendants(id) AS (
                SELECT id FROM posts WHERE id = ?
                UNION
                SELECT child.id
                FROM posts AS child
                JOIN descendants AS parent ON child.reply_to = parent.id
            )
            SELECT id FROM descendants
            """,
            [post_id],
        ).fetchall()
        ordered = [int(row["id"]) for row in descendants]

        if ordered:
            post_reaction_ids = [
                chip.id
                for chip in self.chips.query().where(
                    chipped_to=ordered,
                    kind="reaction",
                ).all()
                if not chip.content.startswith("profile:")
            ]
            if post_reaction_ids:
                self.chips.query().where(id=post_reaction_ids).delete()
            self.posts.query().where(id=ordered).delete()
        invalidate_posts_cache()
        invalidate_analytics_cache(user_id)
        return True

    def toggle_reaction(self, post_id: int, user_id: int, reaction: str) -> Optional[dict]:
        if self._post(post_id) is None:
            return None
        reaction = reaction.strip()
        if not reaction or len(reaction) > 32:
            raise ValueError("Reaction must contain 1 to 32 characters.")

        profile_id = self._profile_id(user_id)

        existing = self.chips.query().where(
            chipped_to=post_id,
            chipped_by=profile_id,
            kind="reaction",
            content=reaction,
        ).first()
        if existing is None:
            self.chips.insert(
                Chip(
                    chipped_to=post_id,
                    chipped_by=profile_id,
                    kind="reaction",
                    content=reaction,
                )
            )
            target = self._post(post_id)
            if target is not None:
                target_type = "comment" if target.is_comment else "post"
                self.notifications.notify(
                    target.user_id,
                    "reaction",
                    f"reacted {reaction} to your {target_type}.",
                    actor_user_id=user_id,
                    target_type=target_type,
                    target_id=post_id,
                )
        else:
            self.chips.query().where(
                chipped_to=post_id,
                chipped_by=profile_id,
                kind="reaction",
                content=reaction,
            ).delete()
        invalidate_posts_cache()
        invalidate_analytics_cache(user_id)
        return self.read(post_id, user_id)
