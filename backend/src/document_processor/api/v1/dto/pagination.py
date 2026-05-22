from __future__ import annotations

from typing import Generic, TypeVar

from document_processor.api.v1.dto._base import CamelCaseModel

T = TypeVar("T")


class Pagination(CamelCaseModel):
    limit: int
    next_cursor: str | None
    has_more: bool


class PaginatedResponse(CamelCaseModel, Generic[T]):
    items: list[T]
    pagination: Pagination
