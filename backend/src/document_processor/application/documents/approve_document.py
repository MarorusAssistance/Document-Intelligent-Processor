from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from document_processor.application.documents.get_document import DocumentNotFound
from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.domain.documents.models import Document, DocumentStatus, StatusHistoryEntry
from document_processor.domain.documents.state_machine import assert_valid_transition


@dataclass(frozen=True)
class ApproveDocumentCommand:
    client_id: str
    document_id: str
    approved_by: str


async def approve_document(
    command: ApproveDocumentCommand,
    documents_repo: DocumentsRepository,
) -> Document:
    document = await documents_repo.get(command.client_id, command.document_id)
    if document is None:
        raise DocumentNotFound(command.client_id, command.document_id)

    assert_valid_transition(document.status, DocumentStatus.approved)

    now = datetime.now(UTC)
    updated = document.model_copy(
        update={
            "status": DocumentStatus.approved,
            "status_history": [
                *document.status_history,
                StatusHistoryEntry(
                    from_status=document.status,
                    to_status=DocumentStatus.approved,
                    at=now,
                    by=command.approved_by,
                ),
            ],
            "updated_at": now,
        }
    )
    await documents_repo.save(updated)
    return updated
