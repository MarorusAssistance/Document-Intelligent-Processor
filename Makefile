.DEFAULT_GOAL := help
SHELL         := /bin/bash

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
INFRA_DIR    := infra
SCRIPTS_DIR  := scripts

.PHONY: help bootstrap dev test lint typecheck openapi-export infra-whatif infra-deploy clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

## ─── Setup ──────────────────────────────────────────────────────────────────

bootstrap: ## First-time local setup (checks prereqs, starts docker, installs deps)
	@bash $(SCRIPTS_DIR)/bootstrap-local.sh

## ─── Development ────────────────────────────────────────────────────────────

dev: ## Start backend (localhost:8000) + frontend (localhost:3000)
	@trap 'kill 0' SIGINT; \
	cd $(BACKEND_DIR) && uv run fastapi dev src/document_processor/main.py --port 8000 & \
	cd $(FRONTEND_DIR) && npm run dev & \
	wait

## ─── Quality ────────────────────────────────────────────────────────────────

test: ## Run unit + integration tests
	cd $(BACKEND_DIR) && uv run pytest tests/unit tests/integration -v --tb=short

lint: ## Run ruff, mypy, prettier
	cd $(BACKEND_DIR) && uv run ruff check src tests
	cd $(BACKEND_DIR) && uv run ruff format --check src tests
	cd $(BACKEND_DIR) && uv run mypy --strict src
	cd $(FRONTEND_DIR) && npx prettier --check .

typecheck: ## Run mypy --strict on backend
	cd $(BACKEND_DIR) && uv run mypy --strict src

## ─── OpenAPI ─────────────────────────────────────────────────────────────────

openapi-export: ## Export OpenAPI schema to docs/api/openapi.json
	uv run python $(SCRIPTS_DIR)/export_openapi.py

## ─── Infrastructure ──────────────────────────────────────────────────────────

infra-whatif: ## Preview Bicep changes (dev environment)
	az deployment sub what-if \
		--location westeurope \
		--template-file $(INFRA_DIR)/main.bicep \
		--parameters $(INFRA_DIR)/parameters/dev.bicepparam

infra-deploy: ## Deploy dev environment to Azure
	az deployment sub create \
		--location westeurope \
		--template-file $(INFRA_DIR)/main.bicep \
		--parameters $(INFRA_DIR)/parameters/dev.bicepparam

## ─── Cleanup ─────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts, caches, and generated files
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/.next $(FRONTEND_DIR)/out 2>/dev/null || true
	rm -f docs/api/openapi.json 2>/dev/null || true
