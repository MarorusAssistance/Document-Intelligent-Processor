# ADR-0006 — Cursor Pagination via Cosmos DB Continuation Token

**Status:** Accepted
**Date:** 2026-05-20

## Context

The `GET /api/v1/documents` endpoint must support paginated listing. The `documents` container can grow to thousands of entries per client. The API needs a pagination strategy that:

- Works efficiently with Cosmos DB.
- Does not require counting total results (expensive in Cosmos).
- Supports stable iteration even when new documents are inserted between page fetches.
- Fits the REST API contract without exposing Cosmos internals to clients.

Two common strategies were evaluated:

1. **Offset pagination:** `?page=3&limit=20`. Requires `OFFSET n SKIP m` in the query, which Cosmos supports but charges for the skipped RUs. Pages become inconsistent if items are inserted between requests.
2. **Cursor pagination:** a server-issued opaque cursor (continuation token) that clients pass back to get the next page. Cosmos DB natively produces continuation tokens for SDK-level pagination.

## Decision

Use **cursor pagination** with Cosmos DB continuation tokens encoded in base64 as an opaque string. The API contract:

```
GET /api/v1/documents?limit=20&cursor=<base64-encoded-token>

Response:
{
  "items": [...],
  "pagination": {
    "limit": 20,
    "nextCursor": "<base64-encoded-token>",
    "hasMore": true
  }
}
```

- `limit` default 20, max 100. Values outside 1–100 return `400 INVALID_PAGINATION_LIMIT`.
- `nextCursor` is absent (or `null`) when there are no more results.
- No `total` count is returned — a separate `GET /count` endpoint will be added if the UI needs it in M2+.
- An invalid cursor returns `400 INVALID_PAGINATION_CURSOR`.

The continuation token is an implementation detail of Cosmos DB. Clients must treat it as opaque and not parse it.

## Consequences

**Better:**
- Cosmos DB produces continuation tokens natively in the SDK — zero extra infrastructure needed.
- Stable pagination: tokens encode the position in the index, not an offset, so inserts between pages do not cause duplicate or skipped items.
- RU cost is proportional to items returned, not items skipped.
- Clients are decoupled from the storage engine; the token format can change without breaking the API contract (since it is opaque).

**Worse:**
- No random access — clients cannot jump to page 5 without fetching pages 1–4.
- No total count — the UI cannot show "Page 3 of 47". A count query would be a separate expensive operation.
- Tokens are tied to the specific query (filters included); changing filters invalidates the cursor.
- Cursors expire if Cosmos DB session state is lost (rare). The API returns `400` in this case; clients restart pagination.

## Alternatives considered

**Offset pagination:** simpler for clients that need "jump to page N". Rejected because Cosmos DB charges RUs for skipped items, results are inconsistent under concurrent inserts, and the HITL UI (M2) does not need random page access — it processes documents sequentially.

**keyset/seek pagination (using `createdAt` + `id` as stable cursor):** more portable across storage backends but requires careful index design and does not leverage Cosmos's native continuation tokens. Adds implementation complexity for the same outcome. Rejected.
