from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from document_processor.application.ports.blob_storage import BlobStorage
from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.application.ports.queue_publisher import QueuePublisher
from document_processor.domain.documents.models import Document, DocumentKind, DocumentSource


@dataclass(frozen=True)
class UploadDocumentCommand:
    client_id: str
    uploaded_by: str
    filename: str
    mime_type: str
    document_kind: DocumentKind
    data: bytes


@dataclass(frozen=True)
class UploadDocumentResult:
    document: Document


async def upload_document(
    command: UploadDocumentCommand,
    documents_repo: DocumentsRepository,
    blob_storage: BlobStorage,
    queue_publisher: QueuePublisher,
) -> UploadDocumentResult:
    # TODO(M1): real blob upload, SHA-256, enqueue OCR job
    now = datetime.now(UTC)
    document = Document(
        client_id=command.client_id,
        document_kind=command.document_kind,
        source=DocumentSource(
            blob_url="",
            filename=command.filename,
            mime_type=command.mime_type,
            size_bytes=len(command.data),
            sha256="",
            uploaded_at=now,
            uploaded_by=command.uploaded_by,
        ),
        created_at=now,
        updated_at=now,
    )
    await documents_repo.save(document)
    return UploadDocumentResult(document=document)
