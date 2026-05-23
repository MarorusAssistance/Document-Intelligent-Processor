from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from document_processor.api.v1.dto._base import CamelCaseModel


class TransitionAction(StrEnum):
    approve = "approve"
    reject = "reject"
    reset = "reset"


class StatusHistoryEntryResponse(CamelCaseModel):
    from_status: str | None = None
    to_status: str
    at: datetime
    by: str
    reason: str | None = None


class DocumentSourceResponse(CamelCaseModel):
    blob_url: str
    filename: str
    mime_type: str
    size_bytes: int
    page_count: int | None = None
    sha256: str
    uploaded_at: datetime
    uploaded_by: str


class ExtractionInfoResponse(CamelCaseModel):
    provider: str
    model_id: str
    model_version: str
    started_at: datetime
    completed_at: datetime | None = None
    overall_confidence: float | None = None
    job_id: str


class ReviewInfoResponse(CamelCaseModel):
    assigned_to: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    correction_count: int = 0


class PushInfoResponse(CamelCaseModel):
    target_erp: str | None = None
    last_attempt_id: str | None = None
    successful_attempt_id: str | None = None
    external_ref: str | None = None
    pushed_at: datetime | None = None


class DocumentResponse(CamelCaseModel):
    id: str
    client_id: str
    document_kind: str
    status: str
    status_history: list[StatusHistoryEntryResponse] = Field(default_factory=list)
    archived_at: datetime | None = None
    source: DocumentSourceResponse
    extraction: ExtractionInfoResponse | None = None
    review: ReviewInfoResponse
    push: PushInfoResponse
    created_at: datetime
    updated_at: datetime


class DocumentListItem(CamelCaseModel):
    id: str
    client_id: str
    document_kind: str
    status: str
    filename: str
    mime_type: str
    correction_count: int
    created_at: datetime
    updated_at: datetime


class PatchDocumentStatusRequest(CamelCaseModel):
    action: TransitionAction
    reason: str | None = None
