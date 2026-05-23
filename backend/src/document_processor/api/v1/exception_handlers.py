from __future__ import annotations

import contextlib

from fastapi import Request, status
from fastapi.responses import JSONResponse

from document_processor.api.v1.dto.errors import ProblemDetails


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id: str | None = None
    with contextlib.suppress(AttributeError):
        trace_id = request.state.trace_id

    problem = ProblemDetails(
        type="about:blank",
        title="Internal Server Error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
        instance=str(request.url),
        trace_id=trace_id,
        code="internal_error",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.model_dump(mode="json", by_alias=True),
        media_type="application/problem+json",
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from fastapi.exceptions import HTTPException

    if not isinstance(exc, HTTPException):
        return await unhandled_exception_handler(request, exc)

    trace_id: str | None = None
    with contextlib.suppress(AttributeError):
        trace_id = request.state.trace_id

    problem = ProblemDetails(
        type="about:blank",
        title=_status_title(exc.status_code),
        status=exc.status_code,
        detail=str(exc.detail),
        instance=str(request.url),
        trace_id=trace_id,
        code=_status_code_slug(exc.status_code),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(mode="json", by_alias=True),
        media_type="application/problem+json",
    )


async def request_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    from fastapi.exceptions import RequestValidationError

    from document_processor.api.v1.dto.errors import FieldError

    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)

    trace_id: str | None = None
    with contextlib.suppress(AttributeError):
        trace_id = request.state.trace_id

    errors = [
        FieldError(
            field=".".join(str(loc) for loc in err["loc"]),
            code="validation_error",
            message=err["msg"],
        )
        for err in exc.errors()
    ]
    problem = ProblemDetails(
        type="about:blank",
        title="Unprocessable Entity",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Request validation failed.",
        instance=str(request.url),
        trace_id=trace_id,
        code="validation_error",
        errors=errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.model_dump(mode="json", by_alias=True),
        media_type="application/problem+json",
    )


def _status_title(status_code: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        501: "Not Implemented",
    }
    return titles.get(status_code, "Error")


def _status_code_slug(status_code: int) -> str:
    slugs = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        501: "not_implemented",
    }
    return slugs.get(status_code, "error")
