from __future__ import annotations

from pydantic import Field

from document_processor.api.v1.dto._base import CamelCaseModel


class FieldError(CamelCaseModel):
    field: str
    code: str
    message: str


class ProblemDetails(CamelCaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    trace_id: str | None = None
    code: str
    errors: list[FieldError] = Field(default_factory=list)
