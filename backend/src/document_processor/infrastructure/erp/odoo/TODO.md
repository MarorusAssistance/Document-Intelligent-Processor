# Odoo ERP Adapter

**Milestone:** M3

Implement the `ERPAdapter` protocol for Odoo Community/Enterprise.

- Endpoint: `POST /api/v1/account.move` (vendor bill creation)
- Auth: API key from Key Vault (`odoo-api-key`)
- Idempotency: use `idempotencyKey` header on Odoo side
