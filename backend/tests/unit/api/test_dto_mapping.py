from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from document_processor.api.v1.dto.mappers import (
    correction_to_response,
    document_to_list_item,
    document_to_response,
    field_to_response,
)
from document_processor.domain.documents.models import (
    Correction,
    DataType,
    Document,
    DocumentKind,
    DocumentSource,
    ExtractedField,
    FieldGroup,
    FieldLocation,
    OcrOriginal,
)
from document_processor.domain.documents.value_objects import BoundingBox, FieldKey, Money


def _now() -> datetime:
    return datetime.now(UTC)


def _make_document() -> Document:
    now = _now()
    return Document(
        client_id="client_abc",
        document_kind=DocumentKind.invoice,
        source=DocumentSource(
            blob_url="https://storage/blob.pdf",
            filename="invoice.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            sha256="deadbeef",
            uploaded_at=now,
            uploaded_by="client_abc",
        ),
        created_at=now,
        updated_at=now,
    )


class TestDocumentToResponse:
    def test_basic_fields(self) -> None:
        doc = _make_document()
        resp = document_to_response(doc)

        assert resp.id == doc.id
        assert resp.client_id == "client_abc"
        assert resp.document_kind == "invoice"
        assert resp.status == "uploaded"

    def test_source_mapped(self) -> None:
        doc = _make_document()
        resp = document_to_response(doc)

        assert resp.source.filename == "invoice.pdf"
        assert resp.source.mime_type == "application/pdf"
        assert resp.source.size_bytes == 2048

    def test_extraction_is_none_when_absent(self) -> None:
        doc = _make_document()
        assert document_to_response(doc).extraction is None

    def test_status_history_empty_by_default(self) -> None:
        doc = _make_document()
        assert document_to_response(doc).status_history == []

    def test_review_defaults(self) -> None:
        doc = _make_document()
        resp = document_to_response(doc)
        assert resp.review.correction_count == 0
        assert resp.review.reviewed_by is None

    def test_serialises_to_camel_case(self) -> None:
        doc = _make_document()
        payload = document_to_response(doc).model_dump(mode="json")
        assert "clientId" in payload
        assert "documentKind" in payload
        assert "client_id" not in payload


class TestDocumentToListItem:
    def test_includes_filename(self) -> None:
        doc = _make_document()
        item = document_to_list_item(doc)
        assert item.filename == "invoice.pdf"
        assert item.correction_count == 0

    def test_serialises_to_camel_case(self) -> None:
        doc = _make_document()
        payload = document_to_list_item(doc).model_dump(mode="json")
        assert "documentKind" in payload


class TestFieldToResponse:
    def _make_field(self, value: str | Money = "INV-001") -> ExtractedField:
        now = _now()
        return ExtractedField(
            client_id="client_abc",
            document_id="doc_123",
            field_key=FieldKey("invoice_number"),
            field_label="Invoice Number",
            field_group=FieldGroup.header,
            value=value,
            data_type=DataType.string,
            ocr_original=OcrOriginal(raw="INV-001", normalized="INV-001", confidence=0.99),
            location=FieldLocation(
                page_number=1,
                bounding_box=BoundingBox(x=0.1, y=0.1, w=0.2, h=0.05),
            ),
            created_at=now,
            updated_at=now,
        )

    def test_string_value_passthrough(self) -> None:
        resp = field_to_response(self._make_field("INV-001"))
        assert resp.value == "INV-001"

    def test_money_value_serialised(self) -> None:
        money = Money(amount=Decimal("1234.56"), currency="EUR")
        resp = field_to_response(self._make_field(money))
        assert isinstance(resp.value, dict)
        assert resp.value["amount"] == "1234.56"
        assert resp.value["currency"] == "EUR"

    def test_bounding_box_mapped(self) -> None:
        resp = field_to_response(self._make_field())
        assert resp.location.bounding_box.x == pytest.approx(0.1)
        assert resp.location.page_number == 1


class TestCorrectionToResponse:
    def test_basic_fields(self) -> None:
        now = _now()
        corr = Correction(
            client_id="client_abc",
            document_id="doc_123",
            field_id="field_456",
            previous_value="OLD",
            new_value="NEW",
            corrected_by="client_abc",
            corrected_at=now,
        )
        resp = correction_to_response(corr)
        assert resp.previous_value == "OLD"
        assert resp.new_value == "NEW"
        assert resp.corrected_by == "client_abc"
