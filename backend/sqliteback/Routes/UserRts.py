"""
Routes/UserRts.py — HTTP endpoints for users.

Auth matrix:
    GET    /users/              authenticated
    POST   /users/              public (registration)
    GET    /users/me            authenticated
    PATCH  /users/me            authenticated (self)
    POST   /users/me/password   authenticated (self)
    DELETE /users/me            authenticated (self, password confirm)
    PATCH  /users/{id}          self or admin
    DELETE /users/{id}          admin only
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.UserFns import UserFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user, invalidate_auth_cache, require_admin
from backend.sqliteback.Models.core import BaseResponse
from backend.sqliteback.Models.UserModels import (
    DataGetMany,
    DataOk,
    DataUser,
    ReqChangePassword,
    ReqCreateUser,
    ReqDeleteSelf,
    ReqUpdateMe,
    ReqUpdateUser,
    UserPublic,
)

users_router = APIRouter(prefix="/users", tags=["user"])
users_fns = UserFns(DB)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _public(user: User) -> UserPublic:
    """Project a full User into the client-safe shape."""
    return UserPublic(
        id=user.id,  # type: ignore
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


def _get_or_404(user_id: int) -> User:
    user = users_fns.read(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )
    return user


# ---------------------------------------------------------------------------
# Collection routes
# ---------------------------------------------------------------------------

@users_router.get("/", response_model=BaseResponse[DataGetMany])
def get_users(
    id: Optional[int] = None,
    username: Optional[str] = None,
    _: User = Depends(get_current_user),
):
    """List users filtered by id and/or username."""
    if id is None and username is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one parameter must be given.",
        )

    filters: dict = {}
    if id is not None:
        filters["id"] = id
    if username:
        filters["username"] = username.strip()

    rows = users_fns.db.query().where(**filters).all()
    payload = DataGetMany(users=[_public(r.to_model()) for r in rows])
    return BaseResponse[DataGetMany](data=payload)


@users_router.post(
    "/",
    response_model=BaseResponse[DataUser],
    status_code=status.HTTP_201_CREATED,
)
def create_user(body: ReqCreateUser):
    """Public registration. Cannot self-elevate to admin."""
    try:
        user = users_fns.create(
            User(
                username=body.username,
                email=body.email,
                password_hash="",          # overwritten in create()
                display_name=body.display_name,
                is_admin=False,            # never trust the client
            ),
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed unexpectedly.",
        )

    return BaseResponse[DataUser](data=DataUser(user=_public(user)))


# ---------------------------------------------------------------------------
# /me routes — must be declared BEFORE /{user_id} so FastAPI doesn't match
# "me" as an integer path param.
# ---------------------------------------------------------------------------

@users_router.get("/me", response_model=BaseResponse[DataUser])
def get_me(me: User = Depends(get_current_user)):
    """Return the authenticated user."""
    return BaseResponse[DataUser](data=DataUser(user=_public(me)))


@users_router.patch("/me", response_model=BaseResponse[DataUser])
def update_me(
    body: ReqUpdateMe,
    me: User = Depends(get_current_user),
):
    """Update the authenticated user's own profile."""
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    if not fields:
        return BaseResponse[DataUser](data=DataUser(user=_public(me)))

    try:
        updated = users_fns.update_fields(me.id, **fields)  # type: ignore[arg-type]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User no longer exists.",
        )

    invalidate_auth_cache()
    return BaseResponse[DataUser](data=DataUser(user=_public(updated)))


@users_router.post("/me/password", response_model=BaseResponse[DataOk])
def change_my_password(
    body: ReqChangePassword,
    request: Request,
    me: User = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if me.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authenticated user has no id.",
        )
    try:
        users_fns.change_password(
            me.id,
            body.current_password,
            body.new_password,
            preserve_session_id=getattr(request.state, "session_id", None),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    invalidate_auth_cache()
    return BaseResponse[DataOk](data=DataOk(ok=True))


@users_router.delete("/me", response_model=BaseResponse[DataOk])
def delete_me(
    body: ReqDeleteSelf,
    me: User = Depends(get_current_user),
):
    """Delete the authenticated user's own account (password required)."""
    from backend.sqliteback.Utils.Hashing import verify_password

    if not verify_password(body.password, me.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password is incorrect.",
        )

    users_fns.delete(me.id)  # type: ignore[arg-type]
    invalidate_auth_cache()
    return BaseResponse[DataOk](data=DataOk(ok=True))


# ---------------------------------------------------------------------------
# /{user_id} routes — self-or-admin for PATCH, admin-only for DELETE
# ---------------------------------------------------------------------------

@users_router.patch("/{user_id}", response_model=BaseResponse[DataUser])
def update_user(
    user_id: int,
    body: ReqUpdateUser,
    me: User = Depends(get_current_user),
):
    """Admin can edit anyone; a user can edit only their own profile."""
    if not me.is_admin and me.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile.",
        )

    _get_or_404(user_id)

    fields = body.model_dump(exclude_unset=True)
    # Non-admins cannot flip flags
    if not me.is_admin:
        fields.pop("is_admin", None)
        fields.pop("is_active", None)
    if not fields:
        current = users_fns.read(user_id)
        return BaseResponse[DataUser](data=DataUser(user=_public(current)))  # type: ignore[arg-type]

    try:
        updated = users_fns.update_fields(user_id, **fields)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )

    invalidate_auth_cache()
    return BaseResponse[DataUser](data=DataUser(user=_public(updated)))


@users_router.delete("/{user_id}", response_model=BaseResponse[DataOk])
def delete_user(
    user_id: int,
    _: User = Depends(require_admin),
):
    """Admin-only hard delete."""
    _get_or_404(user_id)
    users_fns.delete(user_id)
    return BaseResponse[DataOk](data=DataOk(ok=True))