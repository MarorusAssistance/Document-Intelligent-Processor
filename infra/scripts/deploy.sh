#!/usr/bin/env bash
# Deploy Bicep to Azure for the dev environment.
# Requires az login (or OIDC in CI) with Contributor + User Access Administrator.
set -euo pipefail

ENV="${ENV:-dev}"
LOCATION="${LOCATION:-westeurope}"
DEPLOYMENT_NAME="docproc-${ENV}-$(date +%Y%m%d%H%M%S)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Validating Bicep..."
az bicep build --file "${INFRA_DIR}/main.bicep" >/dev/null

echo "==> Running what-if preview..."
az deployment sub what-if \
  --name "${DEPLOYMENT_NAME}-whatif" \
  --location "${LOCATION}" \
  --template-file "${INFRA_DIR}/main.bicep" \
  --parameters "${INFRA_DIR}/parameters/${ENV}.bicepparam"

read -p "Proceed with deployment? [y/N] " -n 1 -r REPLY
echo
if [[ ! "${REPLY}" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

echo "==> Deploying to subscription (env=${ENV}, location=${LOCATION})..."
az deployment sub create \
  --name "${DEPLOYMENT_NAME}" \
  --location "${LOCATION}" \
  --template-file "${INFRA_DIR}/main.bicep" \
  --parameters "${INFRA_DIR}/parameters/${ENV}.bicepparam"

echo "==> Deployment complete: ${DEPLOYMENT_NAME}"
