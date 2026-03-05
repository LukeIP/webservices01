"""Common response schemas."""

from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int


class ErrorResponse(BaseModel):
    detail: str
    code: str
