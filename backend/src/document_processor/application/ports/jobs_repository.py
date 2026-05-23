from __future__ import annotations

from typing import Protocol

from document_processor.domain.jobs.models import Job


class JobsRepository(Protocol):
    async def get(self, client_id: str, job_id: str) -> Job | None: ...

    async def list(
        self,
        client_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Job], str | None]: ...

    async def save(self, job: Job) -> None: ...
