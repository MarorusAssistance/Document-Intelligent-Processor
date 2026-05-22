#!/usr/bin/env bash
# One-time setup: creates App Registration + federated credential for GitHub Actions OIDC.
# Run once per environment. Requires az login with Owner/Contributor + App Admin.
set -euo pipefail

GITHUB_ORG="${GITHUB_ORG:-MarorusAssistance}"
GITHUB_REPO="${GITHUB_REPO:-Document-Intelligent-Processor}"
ENV="${ENV:-dev}"
APP_NAME="sp-docproc-gh-${ENV}"

echo "==> Creating App Registration: ${APP_NAME}"
APP_ID=$(az ad app create --display-name "${APP_NAME}" --query appId -o tsv)
echo "    App ID: ${APP_ID}"

echo "==> Creating Service Principal"
az ad sp create --id "${APP_ID}" >/dev/null

echo "==> Creating federated credential (branch: main)"
az ad app federated-credential create \
  --id "${APP_ID}" \
  --parameters "{
    \"name\": \"github-actions-${ENV}\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:environment:${ENV}\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo ""
echo "==> Set the following GitHub repository variables (Settings > Secrets and variables > Actions > Variables):"
echo "    AZURE_CLIENT_ID      = ${APP_ID}"
echo "    AZURE_TENANT_ID      = ${TENANT_ID}"
echo "    AZURE_SUBSCRIPTION_ID = ${SUBSCRIPTION_ID}"
echo ""
echo "==> Grant Contributor + User Access Administrator on subscription:"
echo "    az role assignment create --assignee ${APP_ID} --role Contributor --scope /subscriptions/${SUBSCRIPTION_ID}"
echo "    az role assignment create --assignee ${APP_ID} --role 'User Access Administrator' --scope /subscriptions/${SUBSCRIPTION_ID}"
echo ""
echo "Done. Run 'make infra-deploy' after setting the variables."
