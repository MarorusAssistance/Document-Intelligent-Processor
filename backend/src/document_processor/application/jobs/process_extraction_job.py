from __future__ import annotations

from dataclasses import dataclass

from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.application.ports.jobs_repository import JobsRepository
from document_processor.application.ports.ocr_provider import OCRProvider
from document_processor.domain.jobs.models import Job


@dataclass(frozen=True)
class ProcessExtractionJobCommand:
    client_id: str
    job_id: str


async def process_extraction_job(
    command: ProcessExtractionJobCommand,
    jobs_repo: JobsRepository,
    documents_repo: DocumentsRepository,
    ocr_provider: OCRProvider,
) -> Job:
    # TODO(M1): implement OCR extraction, field mapping, and document status transition
    raise NotImplementedError("process_extraction_job is implemented in M1")
