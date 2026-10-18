"""
Models/ProfileModels.py — request and response DTOs for profile endpoints.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    about: Optional[str] = Field(default=None, max_length=500)
    powerline: Optional[str] = Field(default=None, max_length=160)
    banner_color: Optional[str] = Field(default=None, max_length=32)
    emoji: Optional[str] = Field(default=None, max_length=4)
    phone: Optional[str] = Field(default=None, max_length=32)
    birthday: Optional[str] = Field(default=None, max_length=16)


class ProfilePublic(BaseModel):
    id: int
    user_id: int
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    about: Optional[str] = None
    powerline: Optional[str] = None
    banner_color: Optional[str] = None
    emoji: Optional[str] = None
    phone: Optional[str] = None
    birthday: Optional[str] = None
    is_owner: bool = False
    followers: int = 0
    following: int = 0
    stars: int = 0
    followed_by_me: bool = False
    starred_by_me: bool = False
    reactions: dict[str, int] = Field(default_factory=dict)
    my_reactions: list[str] = Field(default_factory=list)


class DataProfile(BaseModel):
    profile: ProfilePublic


class DataProfiles(BaseModel):
    profiles: list[ProfilePublic]
