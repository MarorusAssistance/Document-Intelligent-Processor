from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from document_processor.api.v1.dependencies import ClientIdDep, DocumentsRepoDep
from document_processor.api.v1.dto.documents import (
    DocumentListItem,
    DocumentResponse,
    PatchDocumentStatusRequest,
    TransitionAction,
)
from document_processor.api.v1.dto.mappers import document_to_list_item, document_to_response
from document_processor.api.v1.dto.pagination import PaginatedResponse, Pagination
from document_processor.application.documents.approve_document import (
    ApproveDocumentCommand,
    approve_document,
)
from document_processor.application.documents.get_document import (
    DocumentNotFound,
    GetDocumentQuery,
    get_document,
)
from document_processor.application.documents.list_documents import (
    ListDocumentsQuery,
    list_documents,
)
from document_processor.domain.documents.state_machine import InvalidTransition

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.get("", response_model=PaginatedResponse[DocumentListItem])
async def list_documents_endpoint(
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> PaginatedResponse[DocumentListItem]:
    result = await list_documents(
        query=ListDocumentsQuery(client_id=client_id, limit=limit, cursor=cursor),
        documents_repo=repo,
    )
    return PaginatedResponse(
        items=[document_to_list_item(d) for d in result.items],
        pagination=Pagination(
            limit=limit,
            next_cursor=result.next_cursor,
            has_more=result.has_more,
        ),
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(
    document_id: str,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
) -> DocumentResponse:
    try:
        doc = await get_document(
            query=GetDocumentQuery(client_id=client_id, document_id=document_id),
            documents_repo=repo,
        )
    except DocumentNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        ) from None
    return document_to_response(doc)


@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def patch_document_status(
    document_id: str,
    body: PatchDocumentStatusRequest,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
) -> DocumentResponse:
    if body.action == TransitionAction.approve:
        try:
            updated = await approve_document(
                command=ApproveDocumentCommand(
                    client_id=client_id,
                    document_id=document_id,
                    approved_by=client_id,
                ),
                documents_repo=repo,
            )
        except DocumentNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            ) from None
        except InvalidTransition as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return document_to_response(updated)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Action '{body.action}' not yet implemented",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    client_id: ClientIdDep,
    repo: DocumentsRepoDep,
) -> None:
    doc = await repo.get(client_id, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await repo.delete(client_id, document_id)
