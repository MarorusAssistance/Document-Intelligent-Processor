from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from document_processor.application.ports.blob_storage import BlobStorage
from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.application.ports.jobs_repository import JobsRepository
from document_processor.infrastructure.auth.entra_external_id import (
    AuthError,
    extract_bearer_token,
    extract_client_id_from_token,
)


def get_documents_repository(request: Request) -> DocumentsRepository:
    return request.app.state.documents_repo  # type: ignore[no-any-return]


def get_jobs_repository(request: Request) -> JobsRepository:
    return request.app.state.jobs_repo  # type: ignore[no-any-return]


def get_blob_storage(request: Request) -> BlobStorage:
    return request.app.state.blob_storage  # type: ignore[no-any-return]


def get_current_client_id(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    settings = request.app.state.settings

    if settings.auth_dev_bypass and settings.is_development:
        return settings.auth_dev_client_id

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = extract_bearer_token(authorization)
        return extract_client_id_from_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


DocumentsRepoDep = Annotated[DocumentsRepository, Depends(get_documents_repository)]
JobsRepoDep = Annotated[JobsRepository, Depends(get_jobs_repository)]
BlobStorageDep = Annotated[BlobStorage, Depends(get_blob_storage)]
ClientIdDep = Annotated[str, Depends(get_current_client_id)]
