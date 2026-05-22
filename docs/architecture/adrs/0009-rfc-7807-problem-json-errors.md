# ADR-0009 — RFC 7807 Problem+JSON for API Error Responses

**Status:** Accepted
**Date:** 2026-05-20

## Context

The API needs a consistent error response format. Without a standard, every endpoint might return different structures for errors (`{ "error": "..." }`, `{ "message": "..." }`, `{ "detail": "..." }`), making it hard for frontend and integration clients to handle errors programmatically.

FastAPI's default error format (`{ "detail": "..." }`) is acceptable for simple validation errors but lacks machine-readable error codes, request tracing identifiers, and a structured field-level error list.

## Decision

Use **RFC 7807 "Problem Details for HTTP APIs"** (`application/problem+json`) as the standard error response format for all API errors.

Standard fields:

```json
{
  "type": "https://docs.docproc.example.com/errors/document-not-found",
  "title": "Document not found",
  "status": 404,
  "detail": "Document 'doc_01HQ...' does not exist in client 'client_acme'",
  "instance": "/api/v1/documents/doc_01HQ...",
  "traceId": "00-abc123def456...-01",
  "code": "DOCUMENT_NOT_FOUND",
  "errors": [
    { "field": "documentId", "code": "NOT_FOUND", "message": "..." }
  ]
}
```

Extensions beyond RFC 7807:

- **`traceId`:** W3C traceparent string, correlates with Application Insights. Set by `request_id` middleware from the incoming `traceparent` header or generated fresh.
- **`code`:** machine-readable UPPER_SNAKE_CASE error code, stable across API versions. Used by frontend switch statements.
- **`errors`:** array of field-level validation errors (present only for `422` responses and domain validation failures).

A global FastAPI exception handler converts all unhandled exceptions to this format. Validation errors from Pydantic (`RequestValidationError`) are mapped to `422 VALIDATION_FAILED` with per-field `errors`. Domain exceptions (`InvalidTransition`, `ConcurrencyError`) are mapped to `409` with appropriate `code` values.

## Consequences

**Better:**
- Frontend and integration clients have a single, predictable structure for all errors.
- `traceId` connects frontend error logs to backend Application Insights traces — debugging is straightforward.
- Machine-readable `code` allows clients to act on specific error types (e.g., refresh token on `TOKEN_EXPIRED`, retry on `CONCURRENT_MODIFICATION`).
- RFC 7807 is a well-known standard; any HTTP client library or developer familiar with REST APIs recognizes the format.
- The `type` URI serves as documentation link — clicking it opens the error reference page (M6+).

**Worse:**
- Slightly more verbose than a flat `{ "error": "..." }` response.
- The global exception handler must be carefully tested to avoid swallowing unhandled exceptions silently (a 500 with an RFC 7807 body is fine; a 500 with no body is not).
- The `type` URI (`https://docs.docproc.example.com/errors/...`) is a placeholder in M0 — it points to a documentation site that does not exist yet (M6).

## Alternatives considered

**FastAPI default `{ "detail": "..." }`:** simple but lacks `traceId` and machine-readable codes. Frontend must parse human-readable strings to handle errors differently — fragile. Rejected.

**Custom flat format `{ "error": "CODE", "message": "..." }`:** better than FastAPI default but non-standard. Any new developer or integration partner would need to read documentation to understand the format. RFC 7807 is self-documenting via the `type` URI. Rejected.

**GraphQL-style error arrays:** not appropriate for a REST API. Rejected.
