from __future__ import annotations

from enum import StrEnum


class InvoiceFieldKey(StrEnum):
    invoice_number = "invoice_number"
    vendor_name = "vendor_name"
    vendor_tax_id = "vendor_tax_id"
    invoice_date = "invoice_date"
    due_date = "due_date"
    total_amount = "total_amount"
    tax_amount = "tax_amount"
    subtotal_amount = "subtotal_amount"
    currency = "currency"
    purchase_order = "purchase_order"
    payment_terms = "payment_terms"
    customer_name = "customer_name"
    customer_tax_id = "customer_tax_id"
    customer_address = "customer_address"
    vendor_address = "vendor_address"
    line_description = "line_description"
    line_quantity = "line_quantity"
    line_unit_price = "line_unit_price"
    line_amount = "line_amount"
    line_product_code = "line_product_code"
    line_unit = "line_unit"
    line_tax_rate = "line_tax_rate"
