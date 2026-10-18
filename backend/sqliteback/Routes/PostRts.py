"""
Routes/PostRts.py — authenticated post, comment, and reaction endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.PostFns import PostFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user, get_optional_current_user
from backend.sqliteback.Models.core import BaseResponse
from backend.sqliteback.Models.PostModels import (
    DataComments,
    DataOk,
    DataPost,
    DataPosts,
    PostPublic,
    ReqCreateComment,
    ReqCreatePost,
    ReqToggleReaction,
    ReqUpdatePost,
)

posts_router = APIRouter(prefix="/posts", tags=["post"])
post_fns = PostFns(DB)


def _post_response(payload: dict) -> BaseResponse[DataPost]:
    return BaseResponse[DataPost](
        data=DataPost(post=PostPublic.model_validate(payload))
    )


def _raise_domain_error(error: Exception):
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    raise error


@posts_router.get("/me", response_model=BaseResponse[DataPosts])
def get_my_posts(me: User = Depends(get_current_user)):
    posts = post_fns.list_for_user(me.id, me.id)
    return BaseResponse[DataPosts](
        data=DataPosts(posts=[PostPublic.model_validate(post) for post in posts])
    )


@posts_router.get("/", response_model=BaseResponse[DataPosts])
def get_posts(me: Optional[User] = Depends(get_optional_current_user)):
    posts = post_fns.list_all(me.id if me else None)
    return BaseResponse[DataPosts](
        data=DataPosts(posts=[PostPublic.model_validate(post) for post in posts])
    )


@posts_router.post(
    "/",
    response_model=BaseResponse[DataPost],
    status_code=status.HTTP_201_CREATED,
)
def create_post(body: ReqCreatePost, me: User = Depends(get_current_user)):
    try:
        payload = post_fns.create(
            me.id,
            body.content,
            reply_to=body.reply_to,
            is_comment=body.is_comment,
        )
    except (PermissionError, LookupError, ValueError) as error:
        _raise_domain_error(error)
    return _post_response(payload)


@posts_router.get("/{post_id}/comments", response_model=BaseResponse[DataComments])
def get_comments(post_id: int, me: Optional[User] = Depends(get_optional_current_user)):
    try:
        comments = post_fns.comments_for(post_id, me.id if me else None)
    except LookupError as error:
        _raise_domain_error(error)
    return BaseResponse[DataComments](
        data=DataComments(
            post_id=post_id,
            comments=[PostPublic.model_validate(comment) for comment in comments],
        )
    )


@posts_router.post(
    "/{post_id}/comments",
    response_model=BaseResponse[DataPost],
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    body: ReqCreateComment,
    me: User = Depends(get_current_user),
):
    try:
        payload = post_fns.create_comment(
            me.id,
            post_id,
            body.content,
            reply_to=body.reply_to,
        )
    except (PermissionError, LookupError, ValueError) as error:
        _raise_domain_error(error)
    return _post_response(payload)


@posts_router.get("/{post_id}", response_model=BaseResponse[DataPost])
def get_post(post_id: int, me: Optional[User] = Depends(get_optional_current_user)):
    payload = post_fns.read(post_id, me.id if me else None)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )
    return _post_response(payload)


@posts_router.patch("/{post_id}", response_model=BaseResponse[DataPost])
def update_post(
    post_id: int,
    body: ReqUpdatePost,
    me: User = Depends(get_current_user),
):
    fields = body.model_dump(exclude_unset=True)
    try:
        payload = post_fns.update(post_id, me.id, **fields)
    except (PermissionError, LookupError, ValueError) as error:
        _raise_domain_error(error)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )
    return _post_response(payload)


@posts_router.delete("/{post_id}", response_model=BaseResponse[DataOk])
def delete_post(post_id: int, me: User = Depends(get_current_user)):
    try:
        deleted = post_fns.delete(post_id, me.id)
    except (PermissionError, LookupError, ValueError) as error:
        _raise_domain_error(error)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )
    return BaseResponse[DataOk](data=DataOk(ok=True))


@posts_router.post(
    "/{post_id}/reactions",
    response_model=BaseResponse[DataPost],
)
def toggle_reaction(
    post_id: int,
    body: ReqToggleReaction,
    me: User = Depends(get_current_user),
):
    try:
        payload = post_fns.toggle_reaction(post_id, me.id, body.reaction)
    except (PermissionError, LookupError, ValueError) as error:
        _raise_domain_error(error)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )
    return _post_response(payload)
