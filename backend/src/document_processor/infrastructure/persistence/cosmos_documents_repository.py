from __future__ import annotations

import base64
import contextlib
from typing import Any

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import (
    CosmosAccessConditionFailedError,
    CosmosResourceNotFoundError,
)

from document_processor.domain.documents.models import Document


class ConcurrencyError(Exception):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Concurrent modification detected for document '{document_id}'")
        self.document_id = document_id


def _strip_cosmos_meta(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if not k.startswith("_")}


class CosmosDocumentsRepository:
    def __init__(self, container: ContainerProxy) -> None:
        self._container = container
        self._etags: dict[str, str] = {}

    async def get(self, client_id: str, document_id: str) -> Document | None:
        try:
            item: dict[str, Any] = await self._container.read_item(
                item=document_id,
                partition_key=client_id,
            )
            if etag := item.get("_etag"):
                self._etags[document_id] = str(etag)
            return Document.model_validate(_strip_cosmos_meta(item))
        except CosmosResourceNotFoundError:
            return None

    async def list(
        self,
        client_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Document], str | None]:
        cosmos_cursor = base64.b64decode(cursor).decode() if cursor else None
        query = "SELECT * FROM c WHERE c.type = 'Document' ORDER BY c._ts DESC"

        items: list[Document] = []
        next_cosmos_cursor: str | None = None

        pages = self._container.query_items(
            query=query,
            partition_key=client_id,
            max_item_count=limit,
        ).by_page(continuation_token=cosmos_cursor)

        try:
            page = await pages.__anext__()
            async for raw in page:  # type: ignore[attr-defined]
                item = dict(raw)
                if etag := item.get("_etag"):
                    self._etags[item["id"]] = str(etag)
                items.append(Document.model_validate(_strip_cosmos_meta(item)))
            next_cosmos_cursor = pages.continuation_token  # type: ignore[attr-defined]
        except StopAsyncIteration:
            pass

        encoded = (
            base64.b64encode(next_cosmos_cursor.encode()).decode() if next_cosmos_cursor else None
        )
        return items, encoded

    async def save(self, document: Document) -> None:
        body = document.model_dump(mode="json")
        etag = self._etags.get(document.id)

        if etag:
            try:
                result: dict[str, Any] = await self._container.replace_item(
                    item=document.id,
                    body=body,
                    if_match_etag=etag,
                )
            except CosmosAccessConditionFailedError as exc:
                raise ConcurrencyError(document.id) from exc
        else:
            result = await self._container.upsert_item(body=body)

        if new_etag := result.get("_etag"):
            self._etags[document.id] = str(new_etag)

    async def delete(self, client_id: str, document_id: str) -> None:
        with contextlib.suppress(CosmosResourceNotFoundError):
            await self._container.delete_item(item=document_id, partition_key=client_id)
        self._etags.pop(document_id, None)
