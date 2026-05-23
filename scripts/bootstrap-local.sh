#!/usr/bin/env bash
# Bootstrap local development environment from scratch.
# Run once after cloning. Requires: az, docker, uv.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Dependency checks ─────────────────────────────────────────────────────────

command -v az     >/dev/null 2>&1 || { echo "ERROR: Azure CLI not found. https://learn.microsoft.com/cli/azure/install-azure-cli"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not found. https://docs.docker.com/get-docker/"; exit 1; }
command -v uv     >/dev/null 2>&1 || { echo "ERROR: uv not found. curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
command -v node   >/dev/null 2>&1 || { echo "ERROR: Node.js not found. https://nodejs.org/"; exit 1; }

echo "==> Checking Azure login..."
az account show >/dev/null 2>&1 || az login

echo "==> Starting local services (Azurite + Odoo)..."
docker compose -f "${REPO_ROOT}/docker-compose.yml" up -d azurite odoo odoo-db

echo "==> Installing backend dependencies..."
cd "${REPO_ROOT}/backend" && uv sync --all-extras

echo "==> Installing frontend dependencies..."
cd "${REPO_ROOT}/frontend" && npm install

echo "==> Creating .env file (if not already present)..."
cd "${REPO_ROOT}" && cp -n .env.example .env 2>/dev/null && echo "    Created .env from .env.example" || echo "    .env already exists — skipping"

echo ""
echo "Done. Next steps:"
echo "  1. Fill in .env with your Azure resource URLs"
echo "  2. Run 'make dev' to start backend + frontend"
echo "  3. API:      http://localhost:8000/health"
echo "  4. Frontend: http://localhost:3000"
echo "  5. Odoo:     http://localhost:8069 (may take ~2 min first run)"
