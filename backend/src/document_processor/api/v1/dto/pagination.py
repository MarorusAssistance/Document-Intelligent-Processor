from __future__ import annotations

from document_processor.api.v1.dto._base import CamelCaseModel


class Pagination(CamelCaseModel):
    limit: int
    next_cursor: str | None
    has_more: bool


class PaginatedResponse[T](CamelCaseModel):
    items: list[T]
    pagination: Pagination
