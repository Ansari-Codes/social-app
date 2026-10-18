"""
Models/core.py — Shared response envelope.
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    errors: dict[str, str] = Field(default_factory=dict)
    status_code: int = 200
    data: Optional[T] = None