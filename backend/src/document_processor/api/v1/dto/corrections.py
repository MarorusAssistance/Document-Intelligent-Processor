from __future__ import annotations

from datetime import datetime
from typing import Any

from document_processor.api.v1.dto._base import CamelCaseModel


class BoundingBoxResponse(CamelCaseModel):
    x: float
    y: float
    w: float
    h: float


class FieldLocationResponse(CamelCaseModel):
    page_number: int
    bounding_box: BoundingBoxResponse


class OcrOriginalResponse(CamelCaseModel):
    raw: str
    normalized: str
    confidence: float


class ExtractedFieldResponse(CamelCaseModel):
    id: str
    document_id: str
    field_key: str
    field_label: str
    field_group: str
    line_item_index: int | None = None
    value: Any
    data_type: str
    ocr_original: OcrOriginalResponse
    location: FieldLocationResponse
    is_corrected: bool
    correction_count: int
    last_correction_at: datetime | None = None
    last_corrected_by: str | None = None
    created_at: datetime
    updated_at: datetime


class CorrectionResponse(CamelCaseModel):
    id: str
    document_id: str
    field_id: str
    previous_value: Any
    new_value: Any
    reason: str | None = None
    corrected_by: str
    corrected_at: datetime


class CreateCorrectionRequest(CamelCaseModel):
    new_value: Any
    reason: str | None = None
