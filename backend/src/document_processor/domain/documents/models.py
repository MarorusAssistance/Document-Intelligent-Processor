from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field
from ulid import ULID

from document_processor.domain.documents.value_objects import BoundingBox, FieldKey, Money


# ── Enums ──────────────────────────────────────────────────────────────────────


class DocumentKind(StrEnum):
    invoice = "invoice"
    delivery_note = "delivery_note"


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    extracted = "extracted"
    pending_review = "pending_review"
    approved = "approved"
    pushing = "pushing"
    pushed = "pushed"
    rejected = "rejected"
    failed = "failed"


class DataType(StrEnum):
    string = "string"
    number = "number"
    date = "date"
    money = "money"


class FieldGroup(StrEnum):
    header = "header"
    line_item = "line_item"
    footer = "footer"


class TargetErp(StrEnum):
    odoo = "odoo"
    business_central = "business_central"


class PushStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class ErrorCategory(StrEnum):
    transient = "transient"
    permanent = "permanent"
    auth = "auth"
    validation = "validation"
    not_found = "not_found"
    rate_limited = "rate_limited"


# ── Nested value types ─────────────────────────────────────────────────────────


class StatusHistoryEntry(BaseModel):
    from_status: DocumentStatus | None = None
    to_status: DocumentStatus
    at: datetime
    by: str
    reason: str | None = None


class DocumentSource(BaseModel):
    blob_url: str
    filename: str
    mime_type: str
    size_bytes: int
    page_count: int | None = None
    sha256: str
    uploaded_at: datetime
    uploaded_by: str


class ExtractionInfo(BaseModel):
    provider: str
    model_id: str
    model_version: str
    started_at: datetime
    completed_at: datetime | None = None
    overall_confidence: float | None = None
    job_id: str


class ReviewInfo(BaseModel):
    assigned_to: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    correction_count: int = 0


class PushInfo(BaseModel):
    target_erp: TargetErp | None = None
    last_attempt_id: str | None = None
    successful_attempt_id: str | None = None
    external_ref: str | None = None
    pushed_at: datetime | None = None


class OcrOriginal(BaseModel):
    raw: str
    normalized: str
    confidence: float


class FieldLocation(BaseModel):
    page_number: int
    bounding_box: BoundingBox


class PushRequest(BaseModel):
    body_preview: str
    body_size_bytes: int
    sanitized_headers: dict[str, str]


class PushResponse(BaseModel):
    status_code: int
    body_preview: str
    body_size_bytes: int
    latency_ms: int


# ── Entities ───────────────────────────────────────────────────────────────────


def _new_doc_id() -> str:
    return f"doc_{ULID()}"


def _new_field_id() -> str:
    return f"field_{ULID()}"


def _new_correction_id() -> str:
    return f"correction_{ULID()}"


def _new_push_id() -> str:
    return f"push_{ULID()}"


class Document(BaseModel):
    id: str = Field(default_factory=_new_doc_id)
    type: Literal["Document"] = "Document"
    client_id: str
    document_kind: DocumentKind
    status: DocumentStatus = DocumentStatus.uploaded
    status_history: list[StatusHistoryEntry] = Field(default_factory=list)
    archived_at: datetime | None = None
    source: DocumentSource
    extraction: ExtractionInfo | None = None
    review: ReviewInfo = Field(default_factory=ReviewInfo)
    push: PushInfo = Field(default_factory=PushInfo)
    created_at: datetime
    updated_at: datetime


class ExtractedField(BaseModel):
    id: str = Field(default_factory=_new_field_id)
    type: Literal["ExtractedField"] = "ExtractedField"
    client_id: str
    document_id: str
    field_key: FieldKey
    field_label: str
    field_group: FieldGroup
    line_item_index: int | None = None
    value: str | Money
    data_type: DataType
    ocr_original: OcrOriginal
    location: FieldLocation
    is_corrected: bool = False
    correction_count: int = 0
    last_correction_at: datetime | None = None
    last_corrected_by: str | None = None
    created_at: datetime
    updated_at: datetime


class Correction(BaseModel):
    id: str = Field(default_factory=_new_correction_id)
    type: Literal["Correction"] = "Correction"
    client_id: str
    document_id: str
    field_id: str
    previous_value: str | Money
    new_value: str | Money
    reason: str | None = None
    corrected_by: str
    corrected_at: datetime


class PushAttempt(BaseModel):
    id: str = Field(default_factory=_new_push_id)
    type: Literal["PushAttempt"] = "PushAttempt"
    client_id: str
    document_id: str
    job_id: str
    target_erp: TargetErp
    target_endpoint: str
    idempotency_key: str
    attempt_number: int
    status: PushStatus
    request: PushRequest | None = None
    response: PushResponse | None = None
    error_category: ErrorCategory | None = None
    error_message: str | None = None
    external_ref: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
