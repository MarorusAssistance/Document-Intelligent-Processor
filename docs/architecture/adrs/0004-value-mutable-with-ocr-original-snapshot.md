# ADR-0004 — Mutable `value` with Immutable `ocrOriginal` Snapshot

**Status:** Accepted
**Date:** 2026-05-20

## Context

When an OCR provider extracts a field (e.g., `invoice_number = "F-2026/001234"`), that value may be corrected by a human reviewer to `"F-2026/001235"`. The system needs to track:

1. The **current authoritative value** (used by ERP push, the review UI, and all downstream logic).
2. The **original OCR output** (needed for audit trails and ML retraining signal — knowing what the model got wrong).

Three design options were considered for the `ExtractedField` entity:

1. **Immutable field + separate current value:** create a new `ExtractedField` on each correction and mark the old one as superseded.
2. **Mutable `value` with append-only `Correction` log:** `value` is updated in-place; every change is recorded in a separate `Correction` entity.
3. **Mutable `value` + immutable `ocrOriginal` snapshot on the same entity:** `value` reflects the current state; `ocrOriginal` is written once at extraction time and never touched again.

## Decision

Use option 3: **mutable `value` field + immutable `ocrOriginal` snapshot** on the `ExtractedField` entity.

- `value`: mutable, always reflects the current authoritative value.
- `ocrOriginal`: written once (at extraction), never modified. Contains `{ raw, normalized, confidence }`.
- Every correction creates a `Correction` entity (append-only) with `previousValue`, `newValue`, `correctedBy`, `correctedAt`.

## Consequences

**Better:**
- The review UI reads `value` directly — no need to replay a history of corrections to find the current state.
- `ocrOriginal` is always available for audit and ML retraining without querying `Correction` history.
- `Correction` entities provide the full change log when needed, without complicating the main read path.
- `isCorrected`, `correctionCount`, and `lastCorrectedBy` are denormalized on `ExtractedField` to support quick UI rendering without joining `Correction` entities.
- Applying a correction is a single transactional batch: create `Correction` + update `ExtractedField.value` within the same Cosmos DB partition (`clientId`).

**Worse:**
- `ExtractedField` has two representations of "what the field is" (`value` and `ocrOriginal.raw`), which can confuse contributors who expect immutability.
- The repository layer must enforce that `ocrOriginal` is never modified after initial write. This is a convention enforced by code review and tests, not a database constraint.

## Alternatives considered

**Immutable field + new entity per correction (option 1):** complicates the read path significantly — callers must always resolve the "latest" entity. ERP push logic, validation, and the review UI all need to query for the current entity rather than reading `value` directly. Rejected.

**Mutable `value` with `Correction` log but no `ocrOriginal` snapshot (option 2):** loses the original OCR output unless the caller walks the full `Correction` history. For ML retraining, this makes dataset construction expensive. Rejected.
