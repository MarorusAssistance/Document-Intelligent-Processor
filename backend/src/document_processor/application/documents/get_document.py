from __future__ import annotations

from dataclasses import dataclass

from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.domain.documents.models import Document


class DocumentNotFound(Exception):
    def __init__(self, client_id: str, document_id: str) -> None:
        super().__init__(f"Document '{document_id}' not found for client '{client_id}'")
        self.client_id = client_id
        self.document_id = document_id


@dataclass(frozen=True)
class GetDocumentQuery:
    client_id: str
    document_id: str


async def get_document(
    query: GetDocumentQuery,
    documents_repo: DocumentsRepository,
) -> Document:
    document = await documents_repo.get(query.client_id, query.document_id)
    if document is None:
        raise DocumentNotFound(query.client_id, query.document_id)
    return document
