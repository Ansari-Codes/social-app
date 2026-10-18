"""
Routes/ProfileRts.py — endpoints for profile presentation and self-service profile updates.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.ProfileFns import ProfileFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user, invalidate_auth_cache
from backend.sqliteback.Models.core import BaseResponse
from backend.sqliteback.Models.ProfileModels import (
    DataProfile,
    DataProfiles,
    ProfilePublic,
    ProfileUpdatePayload,
)
from backend.sqliteback.Models.PostModels import ReqToggleReaction

profiles_router = APIRouter(prefix="/profiles", tags=["profile"])
profile_fns = ProfileFns(DB)


@profiles_router.get("/me", response_model=BaseResponse[DataProfile])
def get_my_profile(me: User = Depends(get_current_user)):
    payload = profile_fns.read_for_user(me.id, viewer_user_id=me.id, prefetched_user=me)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    return BaseResponse[DataProfile](data=DataProfile(profile=ProfilePublic.model_validate(payload)))


@profiles_router.patch("/me", response_model=BaseResponse[DataProfile])
def update_my_profile(body: ProfileUpdatePayload, me: User = Depends(get_current_user)):
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    if not fields:
        payload = profile_fns.read_for_user(me.id, viewer_user_id=me.id, prefetched_user=me)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found.",
            )
        return BaseResponse[DataProfile](data=DataProfile(profile=ProfilePublic.model_validate(payload)))

    updated = profile_fns.update_for_user(me.id, **fields)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    invalidate_auth_cache()
    return BaseResponse[DataProfile](data=DataProfile(profile=ProfilePublic.model_validate(updated)))


@profiles_router.get("/by-username/{username}", response_model=BaseResponse[DataProfile])
def get_profile_by_username(
    username: str,
    me: User = Depends(get_current_user),
):
    payload = profile_fns.read_by_username(username, viewer_user_id=me.id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    return BaseResponse[DataProfile](data=DataProfile(profile=ProfilePublic.model_validate(payload)))


@profiles_router.get("/{user_id}/followers", response_model=BaseResponse[DataProfiles])
def get_followers(user_id: int, me: User = Depends(get_current_user)):
    if profile_fns.read_for_user(user_id, viewer_user_id=me.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    profiles = profile_fns.list_connections(user_id, me.id, "followers")
    return BaseResponse[DataProfiles](
        data=DataProfiles(profiles=[ProfilePublic.model_validate(item) for item in profiles])
    )


@profiles_router.get("/{user_id}/following", response_model=BaseResponse[DataProfiles])
def get_following(user_id: int, me: User = Depends(get_current_user)):
    if profile_fns.read_for_user(user_id, viewer_user_id=me.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    profiles = profile_fns.list_connections(user_id, me.id, "following")
    return BaseResponse[DataProfiles](
        data=DataProfiles(profiles=[ProfilePublic.model_validate(item) for item in profiles])
    )


def _set_profile_chip(user_id: int, me: User, kind: str, enabled: bool):
    try:
        payload = profile_fns.set_profile_chip(me.id, user_id, kind, enabled)  # type: ignore[arg-type]
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return BaseResponse[DataProfile](
        data=DataProfile(profile=ProfilePublic.model_validate(payload))
    )


@profiles_router.post("/{user_id}/follow", response_model=BaseResponse[DataProfile])
def follow_profile(user_id: int, me: User = Depends(get_current_user)):
    return _set_profile_chip(user_id, me, "follow", True)


@profiles_router.delete("/{user_id}/follow", response_model=BaseResponse[DataProfile])
def unfollow_profile(user_id: int, me: User = Depends(get_current_user)):
    return _set_profile_chip(user_id, me, "follow", False)


@profiles_router.post("/{user_id}/star", response_model=BaseResponse[DataProfile])
def star_profile(user_id: int, me: User = Depends(get_current_user)):
    return _set_profile_chip(user_id, me, "star", True)


@profiles_router.delete("/{user_id}/star", response_model=BaseResponse[DataProfile])
def unstar_profile(user_id: int, me: User = Depends(get_current_user)):
    return _set_profile_chip(user_id, me, "star", False)


@profiles_router.post("/{user_id}/reactions", response_model=BaseResponse[DataProfile])
def toggle_profile_reaction(
    user_id: int,
    body: ReqToggleReaction,
    me: User = Depends(get_current_user),
):
    try:
        payload = profile_fns.toggle_profile_reaction(me.id, user_id, body.reaction)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return BaseResponse[DataProfile](
        data=DataProfile(profile=ProfilePublic.model_validate(payload))
    )


@profiles_router.get("/{user_id}", response_model=BaseResponse[DataProfile])
def get_public_profile(user_id: int, me: User = Depends(get_current_user)):
    payload = profile_fns.read_for_user(user_id, viewer_user_id=me.id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    return BaseResponse[DataProfile](data=DataProfile(profile=ProfilePublic.model_validate(payload)))
