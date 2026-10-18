"""
Models/PostModels.py — request and response DTOs for posts, comments, and reactions.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReqCreatePost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=10000)
    reply_to: Optional[int] = None
    is_comment: bool = False


class ReqUpdatePost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    reply_to: Optional[int] = None
    is_comment: Optional[bool] = None


class ReqCreateComment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=10000)
    reply_to: Optional[int] = None


class ReqToggleReaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reaction: str = Field(min_length=1, max_length=32)


class PostAuthor(BaseModel):
    id: int
    user_id: int
    username: str
    display_name: Optional[str] = None
    emoji: Optional[str] = None
    about: Optional[str] = None
    powerline: Optional[str] = None
    banner_color: Optional[str] = None
    birthday: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    followers: int = 0
    following: int = 0
    stars: int = 0
    followed_by_me: bool = False
    starred_by_me: bool = False


class PostPublic(BaseModel):
    id: int
    root_post_id: int
    user_id: int
    profile: PostAuthor
    content: str
    reply_to: Optional[int] = None
    reply_to_author: Optional[str] = None
    reply_to_snippet: Optional[str] = None
    is_comment: bool
    created_at: str
    updated_at: str
    reactions: dict[str, int]
    my_reactions: list[str]
    comments: int


class DataPost(BaseModel):
    post: PostPublic


class DataPosts(BaseModel):
    posts: list[PostPublic]
    next_cursor: Optional[int] = None


class DataComments(BaseModel):
    post_id: int
    comments: list[PostPublic]


class DataOk(BaseModel):
    ok: bool = True
