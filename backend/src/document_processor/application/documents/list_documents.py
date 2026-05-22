from __future__ import annotations

from dataclasses import dataclass

from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.domain.documents.models import Document


@dataclass(frozen=True)
class ListDocumentsQuery:
    client_id: str
    limit: int = 20
    cursor: str | None = None


@dataclass(frozen=True)
class ListDocumentsResult:
    items: list[Document]
    next_cursor: str | None
    has_more: bool


async def list_documents(
    query: ListDocumentsQuery,
    documents_repo: DocumentsRepository,
) -> ListDocumentsResult:
    items, next_cursor = await documents_repo.list(
        query.client_id,
        limit=query.limit,
        cursor=query.cursor,
    )
    return ListDocumentsResult(
        items=items,
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )
