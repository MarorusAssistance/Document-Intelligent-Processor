# ADR-0003 — Entity-per-cell for Invoice Line Items

**Status:** Accepted
**Date:** 2026-05-20

## Context

Invoices contain line items — typically 1–50 rows, each with fields like description, quantity, unit price, and amount. These fields need to be extracted by OCR, corrected by human reviewers, and audited via `Correction` records.

Two storage approaches were evaluated for line item fields within `ExtractedField`:

1. **Array-inline:** embed all line items as a nested array inside the parent `Document` or a single `ExtractedField` per line (`{ lineItems: [{ description: "...", quantity: 1, ... }] }`).
2. **Entity-per-cell:** one `ExtractedField` document per cell — each field of each line item is its own entity with `lineItemIndex` and `fieldKey` (e.g., `line_description`, `line_quantity`).

## Decision

Use **entity-per-cell** from M0 onwards. Each cell of a line item table is an independent `ExtractedField` document in Cosmos DB, identified by the combination of `documentId`, `lineItemIndex`, and `fieldKey`.

## Consequences

**Better:**
- Corrections apply to a single field of a single line item — the `Correction` entity already references a `fieldId`, which maps cleanly to one cell.
- Confidence scores, bounding boxes, and `ocrOriginal` snapshots are stored per-cell, enabling fine-grained UI highlighting and retraining signal per cell.
- Cosmos DB item size limit (2MB) is not a risk: a 50-line invoice with 6 fields per line produces 300 small documents rather than 1 large nested document.
- No refactor needed at M3 (ERP push maps cell-by-cell to ERP line fields) or M4 (delivery note has a similar table structure).
- Filtering and updating individual cells uses standard partition-key queries.

**Worse:**
- More documents in Cosmos DB (300 instead of 1 for a 50-line invoice). At free tier (1000 RU/s shared), the RU cost of a full document fetch increases (one read-many vs. one read-one). Acceptable given the expected volume.
- List endpoint for fields (`GET /documents/{id}/fields`) must query and paginate across many entities.
- Application code must assemble line items from individual cells when building the HITL review view.

## Alternatives considered

**Array-inline (fields as nested JSON):** simpler to fetch (one document read). However, corrections would target an array index rather than a stable entity ID, making the `Correction` audit log brittle. Applying a correction would require replacing the entire array (no atomic partial update in Cosmos without stored procedures). The Cosmos 2MB item limit becomes a real risk for invoices with many lines and bounding box data. A refactor at M3 to support ERP line-level mapping would be expensive. Rejected.

**Hybrid (header fields as entities, line items as array):** avoids the 2MB risk for header fields but still makes per-cell corrections awkward for line items. Rejected as a half-measure.
