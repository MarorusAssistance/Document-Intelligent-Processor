from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── General ───────────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    # ── Azure identity ────────────────────────────────────────────────────────
    azure_tenant_id: str = ""
    azure_subscription_id: str = ""

    # ── Cosmos DB ─────────────────────────────────────────────────────────────
    cosmos_endpoint: str = ""
    cosmos_database: str = "docproc"

    # ── Service Bus ───────────────────────────────────────────────────────────
    service_bus_namespace: str = ""
    service_bus_queue_ocr: str = "ocr-extraction-jobs"

    # ── Document Intelligence ─────────────────────────────────────────────────
    doc_intelligence_endpoint: str = ""

    # ── Key Vault ─────────────────────────────────────────────────────────────
    key_vault_url: str = ""

    # ── Application Insights ──────────────────────────────────────────────────
    application_insights_connection_string: str = ""

    # ── Blob Storage ──────────────────────────────────────────────────────────
    storage_account_url: str = ""
    storage_use_azurite: bool = False

    # ── Odoo ──────────────────────────────────────────────────────────────────
    odoo_url: str = ""
    odoo_db: str = "docproc"
    odoo_username: str = "admin"

    # ── Auth ──────────────────────────────────────────────────────────────────
    auth_dev_bypass: bool = False
    auth_dev_client_id: str = "client_local_dev"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
