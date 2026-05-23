from __future__ import annotations

import base64
from typing import Any

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import (
    CosmosAccessConditionFailedError,
    CosmosResourceNotFoundError,
)

from document_processor.domain.jobs.models import Job
from document_processor.infrastructure.persistence.cosmos_documents_repository import (
    ConcurrencyError,
    _strip_cosmos_meta,
)


class CosmosJobsRepository:
    def __init__(self, container: ContainerProxy) -> None:
        self._container = container
        self._etags: dict[str, str] = {}

    async def get(self, client_id: str, job_id: str) -> Job | None:
        try:
            item: dict[str, Any] = await self._container.read_item(
                item=job_id,
                partition_key=client_id,
            )
            if etag := item.get("_etag"):
                self._etags[job_id] = str(etag)
            return Job.model_validate(_strip_cosmos_meta(item))
        except CosmosResourceNotFoundError:
            return None

    async def list(
        self,
        client_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Job], str | None]:
        cosmos_cursor = base64.b64decode(cursor).decode() if cursor else None
        query = "SELECT * FROM c WHERE c.type = 'Job' ORDER BY c._ts DESC"

        jobs: list[Job] = []
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
                jobs.append(Job.model_validate(_strip_cosmos_meta(item)))
            next_cosmos_cursor = pages.continuation_token  # type: ignore[attr-defined]
        except StopAsyncIteration:
            pass

        encoded = (
            base64.b64encode(next_cosmos_cursor.encode()).decode() if next_cosmos_cursor else None
        )
        return jobs, encoded

    async def save(self, job: Job) -> None:
        body = job.model_dump(mode="json")
        etag = self._etags.get(job.id)

        if etag:
            try:
                result: dict[str, Any] = await self._container.replace_item(
                    item=job.id,
                    body=body,
                    if_match_etag=etag,
                )
            except CosmosAccessConditionFailedError as exc:
                raise ConcurrencyError(job.id) from exc
        else:
            result = await self._container.upsert_item(body=body)

        if new_etag := result.get("_etag"):
            self._etags[job.id] = str(new_etag)
