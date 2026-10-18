"""
Routes/FeedRts.py — authenticated feed endpoint.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.FeedFns import FeedFns
from backend.sqliteback.Helpers.AuthHelp import get_optional_current_user
from backend.sqliteback.Models.core import BaseResponse
from backend.sqliteback.Models.PostModels import DataPosts, PostPublic

feed_router = APIRouter(prefix="/feed", tags=["feed"])
feed_fns = FeedFns(DB)


@feed_router.get("/", response_model=BaseResponse[DataPosts])
def get_feed(
    limit: int = Query(default=20, ge=1, le=50),
    before_id: Optional[int] = Query(default=None, ge=1),
    me: Optional[User] = Depends(get_optional_current_user),
):
    posts, next_cursor = feed_fns.list_page(
        me.id if me else None,
        limit=limit,
        before_id=before_id,
    )
    payload = DataPosts(
        posts=[PostPublic.model_validate(post) for post in posts],
        next_cursor=next_cursor,
    )
    return BaseResponse[DataPosts](data=payload)
