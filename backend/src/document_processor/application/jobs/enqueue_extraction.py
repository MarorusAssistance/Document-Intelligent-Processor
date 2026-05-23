from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from document_processor.application.ports.jobs_repository import JobsRepository
from document_processor.application.ports.queue_publisher import QueuePublisher
from document_processor.domain.jobs.models import Job, JobKind, OcrExtractPayload


@dataclass(frozen=True)
class EnqueueExtractionCommand:
    client_id: str
    document_id: str
    blob_url: str
    model_id: str = "prebuilt-invoice"
    model_version: str = "2024-11-30"


@dataclass(frozen=True)
class EnqueueExtractionResult:
    job: Job


async def enqueue_extraction(
    command: EnqueueExtractionCommand,
    jobs_repo: JobsRepository,
    queue_publisher: QueuePublisher,
) -> EnqueueExtractionResult:
    now = datetime.now(UTC)
    job = Job(
        client_id=command.client_id,
        document_id=command.document_id,
        job_kind=JobKind.ocr_extract,
        payload=OcrExtractPayload(
            model_id=command.model_id,
            model_version=command.model_version,
            blob_url=command.blob_url,
        ),
        created_at=now,
    )
    await jobs_repo.save(job)
    await queue_publisher.publish(
        "ocr-extraction-jobs", {"jobId": job.id, "clientId": job.client_id}
    )
    return EnqueueExtractionResult(job=job)
