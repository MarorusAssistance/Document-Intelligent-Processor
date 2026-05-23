from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from ulid import ULID

# ── Enums ──────────────────────────────────────────────────────────────────────


class JobKind(StrEnum):
    ocr_extract = "ocr_extract"
    push_to_erp = "push_to_erp"
    classify_document = "classify_document"


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    dead_letter = "dead_letter"


# ── Payload discriminated union ────────────────────────────────────────────────


class OcrExtractPayload(BaseModel):
    kind: Literal["ocr_extract"] = "ocr_extract"
    model_id: str
    model_version: str
    blob_url: str


class PushToErpPayload(BaseModel):
    kind: Literal["push_to_erp"] = "push_to_erp"
    target_erp: str


class ClassifyDocumentPayload(BaseModel):
    kind: Literal["classify_document"] = "classify_document"
    blob_url: str


JobPayload = Annotated[
    OcrExtractPayload | PushToErpPayload | ClassifyDocumentPayload,
    Field(discriminator="kind"),
]


# ── Result discriminated union ─────────────────────────────────────────────────


class OcrExtractResult(BaseModel):
    kind: Literal["ocr_extract"] = "ocr_extract"
    fields_count: int
    overall_confidence: float


class PushToErpResult(BaseModel):
    kind: Literal["push_to_erp"] = "push_to_erp"
    external_ref: str


class ClassifyDocumentResult(BaseModel):
    kind: Literal["classify_document"] = "classify_document"
    document_kind: str


JobResult = Annotated[
    OcrExtractResult | PushToErpResult | ClassifyDocumentResult,
    Field(discriminator="kind"),
]


# ── Entity ─────────────────────────────────────────────────────────────────────


def _new_job_id() -> str:
    return f"job_{ULID()}"


class Job(BaseModel):
    id: str = Field(default_factory=_new_job_id)
    type: Literal["Job"] = "Job"
    client_id: str
    document_id: str
    job_kind: JobKind
    status: JobStatus = JobStatus.pending
    payload: JobPayload
    result: JobResult | None = None
    attempt_number: int = 1
    max_attempts: int = 5
    next_retry_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
