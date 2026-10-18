"""
Functions/FeedFns.py — feed aggregation over published posts.
"""

from typing import Optional

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB
from backend.sqliteback.Functions.PostFns import PostFns


class FeedFns:
    def __init__(self, db: Database = DB):
        self.posts = PostFns(db)

    def list_posts(self, viewer_user_id: Optional[int] = None) -> list[dict]:
        """Return published posts; comments remain available in post threads."""
        return self.posts.feed(viewer_user_id)

    def list_page(
        self,
        viewer_user_id: Optional[int] = None,
        *,
        limit: int = 20,
        before_id: Optional[int] = None,
    ) -> tuple[list[dict], Optional[int]]:
        return self.posts.feed_page(viewer_user_id, limit=limit, before_id=before_id)
