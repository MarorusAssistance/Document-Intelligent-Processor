from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from document_processor.api.v1.dependencies import ClientIdDep, DocumentsRepoDep
from document_processor.api.v1.dto.corrections import (
    CorrectionResponse,
    CreateCorrectionRequest,
    ExtractedFieldResponse,
)
from document_processor.api.v1.dto.mappers import correction_to_response
from document_processor.api.v1.dto.pagination import PaginatedResponse, Pagination
from document_processor.application.documents.apply_correction import (
    ApplyCorrectionCommand,
    apply_correction,
)
from document_processor.application.documents.get_document import DocumentNotFound

router = APIRouter(prefix="/api/v1/documents", tags=["corrections"])


@router.get("/{document_id}/fields", response_model=PaginatedResponse[ExtractedFieldResponse])
async def list_fields(
    document_id: str,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
) -> PaginatedResponse[ExtractedFieldResponse]:
    doc = await repo.get(client_id, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # TODO(M1): fields stored separately; for now return empty
    return PaginatedResponse(
        items=[],
        pagination=Pagination(limit=limit, next_cursor=None, has_more=False),
    )


@router.get(
    "/{document_id}/fields/{field_id}",
    response_model=ExtractedFieldResponse,
)
async def get_field(
    document_id: str,
    field_id: str,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
) -> ExtractedFieldResponse:
    doc = await repo.get(client_id, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")


@router.post(
    "/{document_id}/fields/{field_id}/corrections",
    response_model=CorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_correction(
    document_id: str,
    field_id: str,
    body: CreateCorrectionRequest,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
) -> CorrectionResponse:
    try:
        result = await apply_correction(
            command=ApplyCorrectionCommand(
                client_id=client_id,
                document_id=document_id,
                field_id=field_id,
                new_value=body.new_value,
                corrected_by=client_id,
                reason=body.reason,
            ),
            documents_repo=repo,
        )
    except DocumentNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        ) from None
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc
    return correction_to_response(result.correction)


@router.get(
    "/{document_id}/corrections",
    response_model=PaginatedResponse[CorrectionResponse],
)
async def list_corrections(
    document_id: str,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> PaginatedResponse[CorrectionResponse]:
    doc = await repo.get(client_id, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # TODO(M2): corrections stored separately
    return PaginatedResponse(
        items=[],
        pagination=Pagination(limit=limit, next_cursor=None, has_more=False),
    )
