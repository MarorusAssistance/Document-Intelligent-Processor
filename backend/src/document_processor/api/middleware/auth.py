from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from document_processor.infrastructure.auth.entra_external_id import (
    AuthError,
    extract_bearer_token,
    extract_client_id_from_token,
)

_EXEMPT_PREFIXES = ("/health", "/api/v1/version", "/docs", "/redoc", "/openapi.json")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        settings = request.app.state.settings

        if settings.auth_dev_bypass and settings.is_development:
            request.state.client_id = settings.auth_dev_client_id
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            token = extract_bearer_token(authorization)
            client_id = extract_client_id_from_token(token)
        except AuthError as exc:
            return JSONResponse(
                status_code=401,
                content={"detail": exc.detail},
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.client_id = client_id
        return await call_next(request)
