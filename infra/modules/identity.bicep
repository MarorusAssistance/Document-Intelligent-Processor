param apiIdentityName string
param workerIdentityName string
param location string

// Resource names for existing resource references
param cosmosAccountName string
param storageAccountName string
param serviceBusNamespaceName string
param keyVaultName string
param docIntelligenceName string
param appInsightsName string

// ── User-Assigned Managed Identities ──────────────────────────────────────────

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: apiIdentityName
  location: location
}

resource workerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: workerIdentityName
  location: location
}

// ── Existing resource references ──────────────────────────────────────────────

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: cosmosAccountName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' existing = {
  name: serviceBusNamespaceName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource docIntelligence 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' existing = {
  name: docIntelligenceName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// ── Well-known Azure built-in role definition IDs ─────────────────────────────

var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var storageBlobDataReaderRoleId      = '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
var serviceBusDataSenderRoleId       = '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
var serviceBusDataReceiverRoleId     = '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0'
var keyVaultSecretsUserRoleId        = '4633458b-17de-408a-b874-0445c86b69e6'
var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'
var cognitiveServicesUserRoleId      = 'a97b65f3-24c7-4388-baec-2e87135dc908'

// Cosmos DB data-plane built-in role IDs (not Azure RBAC — Cosmos SQL RBAC)
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// ── Cosmos DB data-plane role assignments (SQL RBAC) ──────────────────────────

resource cosmosRoleApi 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, apiIdentity.id, 'cosmos-data-contributor')
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: apiIdentity.properties.principalId
    scope: cosmosAccount.id
  }
}

resource cosmosRoleWorker 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, workerIdentity.id, 'cosmos-data-contributor')
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: workerIdentity.properties.principalId
    scope: cosmosAccount.id
  }
}

// ── Storage Blob role assignments ─────────────────────────────────────────────

resource storageBlobContributorApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, apiIdentity.id, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageBlobReaderWorker 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, workerIdentity.id, storageBlobDataReaderRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataReaderRoleId)
    principalId: workerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Service Bus role assignments ──────────────────────────────────────────────

resource sbSenderApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: serviceBusNamespace
  name: guid(serviceBusNamespace.id, apiIdentity.id, serviceBusDataSenderRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataSenderRoleId)
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource sbReceiverWorker 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: serviceBusNamespace
  name: guid(serviceBusNamespace.id, workerIdentity.id, serviceBusDataReceiverRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataReceiverRoleId)
    principalId: workerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Key Vault Secrets User role assignments ───────────────────────────────────

resource kvSecretsApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, apiIdentity.id, keyVaultSecretsUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource kvSecretsWorker 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, workerIdentity.id, keyVaultSecretsUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: workerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Document Intelligence — Cognitive Services User (worker only) ─────────────

resource cogServicesWorker 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: docIntelligence
  name: guid(docIntelligence.id, workerIdentity.id, cognitiveServicesUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
    principalId: workerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Monitoring Metrics Publisher ──────────────────────────────────────────────

resource monitoringApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, apiIdentity.id, monitoringMetricsPublisherRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource monitoringWorker 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, workerIdentity.id, monitoringMetricsPublisherRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: workerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output apiIdentityId string = apiIdentity.id
output apiIdentityClientId string = apiIdentity.properties.clientId
output workerIdentityId string = workerIdentity.id
output workerIdentityClientId string = workerIdentity.properties.clientId
