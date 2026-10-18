"""
Models/AnalyticsModels.py — dashboard activity analytics response shapes.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ActivityPoint(BaseModel):
    date: str
    followers: int
    stars: int
    posts: int = 0
    reactions: int = 0


class DashboardAnalytics(BaseModel):
    days: int
    total_posts: int
    total_comments: int
    total_reactions: int
    dominant_reaction: Optional[str] = None
    dominant_reaction_count: int = 0
    time_series: list[ActivityPoint]
    reaction_breakdown: dict[str, int] = Field(default_factory=dict)
    total_followers: int = 0
    total_stars: int = 0
    total_following: int = 0
    engagement_rate: float = 0.0
    top_posts: list[dict[str, Any]] = Field(default_factory=list)
