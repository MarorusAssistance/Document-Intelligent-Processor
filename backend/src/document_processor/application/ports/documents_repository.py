from __future__ import annotations

from typing import Protocol

from document_processor.domain.documents.models import Document


class DocumentsRepository(Protocol):
    async def get(self, client_id: str, document_id: str) -> Document | None: ...

    async def list(
        self,
        client_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Document], str | None]: ...

    async def save(self, document: Document) -> None: ...

    async def delete(self, client_id: str, document_id: str) -> None: ...
