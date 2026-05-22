from __future__ import annotations

from typing import Any

from document_processor.domain.documents.models import Correction, Document, ExtractedField
from document_processor.domain.documents.value_objects import Money
from document_processor.domain.jobs.models import Job
from document_processor.api.v1.dto.corrections import (
    BoundingBoxResponse,
    CorrectionResponse,
    ExtractedFieldResponse,
    FieldLocationResponse,
    OcrOriginalResponse,
)
from document_processor.api.v1.dto.documents import (
    DocumentListItem,
    DocumentResponse,
    DocumentSourceResponse,
    ExtractionInfoResponse,
    PushInfoResponse,
    ReviewInfoResponse,
    StatusHistoryEntryResponse,
)
from document_processor.api.v1.dto.jobs import JobListItem, JobResponse


def _value_to_wire(value: str | Money) -> Any:
    if isinstance(value, Money):
        return {"amount": str(value.amount), "currency": value.currency}
    return value


def document_to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        client_id=doc.client_id,
        document_kind=doc.document_kind.value,
        status=doc.status.value,
        status_history=[
            StatusHistoryEntryResponse(
                from_status=e.from_status.value if e.from_status else None,
                to_status=e.to_status.value,
                at=e.at,
                by=e.by,
                reason=e.reason,
            )
            for e in doc.status_history
        ],
        archived_at=doc.archived_at,
        source=DocumentSourceResponse(
            blob_url=doc.source.blob_url,
            filename=doc.source.filename,
            mime_type=doc.source.mime_type,
            size_bytes=doc.source.size_bytes,
            page_count=doc.source.page_count,
            sha256=doc.source.sha256,
            uploaded_at=doc.source.uploaded_at,
            uploaded_by=doc.source.uploaded_by,
        ),
        extraction=ExtractionInfoResponse(
            provider=doc.extraction.provider,
            model_id=doc.extraction.model_id,
            model_version=doc.extraction.model_version,
            started_at=doc.extraction.started_at,
            completed_at=doc.extraction.completed_at,
            overall_confidence=doc.extraction.overall_confidence,
            job_id=doc.extraction.job_id,
        )
        if doc.extraction
        else None,
        review=ReviewInfoResponse(
            assigned_to=doc.review.assigned_to,
            reviewed_by=doc.review.reviewed_by,
            reviewed_at=doc.review.reviewed_at,
            correction_count=doc.review.correction_count,
        ),
        push=PushInfoResponse(
            target_erp=doc.push.target_erp.value if doc.push.target_erp else None,
            last_attempt_id=doc.push.last_attempt_id,
            successful_attempt_id=doc.push.successful_attempt_id,
            external_ref=doc.push.external_ref,
            pushed_at=doc.push.pushed_at,
        ),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def document_to_list_item(doc: Document) -> DocumentListItem:
    return DocumentListItem(
        id=doc.id,
        client_id=doc.client_id,
        document_kind=doc.document_kind.value,
        status=doc.status.value,
        filename=doc.source.filename,
        mime_type=doc.source.mime_type,
        correction_count=doc.review.correction_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def field_to_response(field: ExtractedField) -> ExtractedFieldResponse:
    return ExtractedFieldResponse(
        id=field.id,
        document_id=field.document_id,
        field_key=str(field.field_key),
        field_label=field.field_label,
        field_group=field.field_group.value,
        line_item_index=field.line_item_index,
        value=_value_to_wire(field.value),
        data_type=field.data_type.value,
        ocr_original=OcrOriginalResponse(
            raw=field.ocr_original.raw,
            normalized=field.ocr_original.normalized,
            confidence=field.ocr_original.confidence,
        ),
        location=FieldLocationResponse(
            page_number=field.location.page_number,
            bounding_box=BoundingBoxResponse(
                x=field.location.bounding_box.x,
                y=field.location.bounding_box.y,
                w=field.location.bounding_box.w,
                h=field.location.bounding_box.h,
            ),
        ),
        is_corrected=field.is_corrected,
        correction_count=field.correction_count,
        last_correction_at=field.last_correction_at,
        last_corrected_by=field.last_corrected_by,
        created_at=field.created_at,
        updated_at=field.updated_at,
    )


def correction_to_response(corr: Correction) -> CorrectionResponse:
    return CorrectionResponse(
        id=corr.id,
        document_id=corr.document_id,
        field_id=corr.field_id,
        previous_value=_value_to_wire(corr.previous_value),
        new_value=_value_to_wire(corr.new_value),
        reason=corr.reason,
        corrected_by=corr.corrected_by,
        corrected_at=corr.corrected_at,
    )


def job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        client_id=job.client_id,
        document_id=job.document_id,
        job_kind=job.job_kind.value,
        status=job.status.value,
        payload=job.payload.model_dump(mode="json"),
        result=job.result.model_dump(mode="json") if job.result else None,
        attempt_number=job.attempt_number,
        max_attempts=job.max_attempts,
        next_retry_at=job.next_retry_at,
        last_error=job.last_error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_ms=job.duration_ms,
    )


def job_to_list_item(job: Job) -> JobListItem:
    return JobListItem(
        id=job.id,
        client_id=job.client_id,
        document_id=job.document_id,
        job_kind=job.job_kind.value,
        status=job.status.value,
        attempt_number=job.attempt_number,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
