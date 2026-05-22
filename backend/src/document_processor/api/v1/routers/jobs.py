from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from document_processor.api.v1.dependencies import ClientIdDep, JobsRepoDep
from document_processor.api.v1.dto.jobs import JobListItem, JobResponse
from document_processor.api.v1.dto.mappers import job_to_list_item, job_to_response
from document_processor.api.v1.dto.pagination import PaginatedResponse, Pagination

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobListItem])
async def list_jobs(
    client_id: ClientIdDep,
    repo: JobsRepoDep,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> PaginatedResponse[JobListItem]:
    items, next_cursor = await repo.list(client_id, limit=limit, cursor=cursor)
    return PaginatedResponse(
        items=[job_to_list_item(j) for j in items],
        pagination=Pagination(
            limit=limit,
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
        ),
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    client_id: ClientIdDep,
    repo: JobsRepoDep,
) -> JobResponse:
    job = await repo.get(client_id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job_to_response(job)
