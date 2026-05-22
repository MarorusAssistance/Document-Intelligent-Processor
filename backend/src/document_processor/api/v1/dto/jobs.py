from __future__ import annotations

from datetime import datetime
from typing import Any

from document_processor.api.v1.dto._base import CamelCaseModel


class JobResponse(CamelCaseModel):
    id: str
    client_id: str
    document_id: str
    job_kind: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    attempt_number: int
    max_attempts: int
    next_retry_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None


class JobListItem(CamelCaseModel):
    id: str
    client_id: str
    document_id: str
    job_kind: str
    status: str
    attempt_number: int
    created_at: datetime
    completed_at: datetime | None = None
