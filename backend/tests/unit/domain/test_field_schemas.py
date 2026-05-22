from __future__ import annotations

from document_processor.domain.documents.field_schemas.invoice import InvoiceFieldKey


class TestInvoiceFieldKey:
    def test_all_values_are_strings(self) -> None:
        for key in InvoiceFieldKey:
            assert isinstance(key.value, str)

    def test_values_are_unique(self) -> None:
        values = [k.value for k in InvoiceFieldKey]
        assert len(values) == len(set(values))

    def test_values_are_snake_case(self) -> None:
        for key in InvoiceFieldKey:
            assert key.value == key.value.lower()
            assert " " not in key.value

    def test_header_fields_present(self) -> None:
        assert InvoiceFieldKey.invoice_number == "invoice_number"
        assert InvoiceFieldKey.vendor_name == "vendor_name"
        assert InvoiceFieldKey.total_amount == "total_amount"
        assert InvoiceFieldKey.invoice_date == "invoice_date"

    def test_line_item_fields_present(self) -> None:
        assert InvoiceFieldKey.line_description == "line_description"
        assert InvoiceFieldKey.line_quantity == "line_quantity"
        assert InvoiceFieldKey.line_unit_price == "line_unit_price"
        assert InvoiceFieldKey.line_amount == "line_amount"

    def test_minimum_key_count(self) -> None:
        assert len(InvoiceFieldKey) >= 20
