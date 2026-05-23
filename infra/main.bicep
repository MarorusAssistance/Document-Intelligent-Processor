targetScope = 'subscription'

@description('Base name for all resources')
param baseName string = 'docproc'

@description('Environment name')
@allowed(['dev', 'prod'])
param env string = 'dev'

@description('Region abbreviation for naming (e.g. weu)')
param region string = 'weu'

@description('Azure region for deployment')
param location string = 'westeurope'

@description('Enable Cosmos DB free tier (one per subscription)')
param enableFreeTier bool = true

@description('Set true after first CAE provision to avoid re-provisioning (westeurope AKS capacity)')
param existingCae bool = false

@description('Azure region for Container Apps resources (may differ from main location due to AKS capacity)')
param caLocation string = 'westeurope'

// ── Naming ────────────────────────────────────────────────────────────────────

// Compute RG name inline — module outputs are not available at deployment start (BCP120)
var rgName = 'rg-${baseName}-${env}-${region}'

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: rgName
  location: location
}

module naming 'modules/naming.bicep' = {
  name: 'naming'
  scope: subscription()
  params: {
    baseName: baseName
    env: env
    region: region
  }
}

// ── Monitoring (deployed first — other modules depend on outputs) ──────────────

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    logAnalyticsName: naming.outputs.logAnalyticsName
    appInsightsName: naming.outputs.appInsightsName
    location: location
  }
}

// ── Storage ───────────────────────────────────────────────────────────────────

module storage 'modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    storageAccountName: naming.outputs.storageAccountName
    location: location
  }
}

// ── Cosmos DB ─────────────────────────────────────────────────────────────────

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  scope: rg
  params: {
    cosmosAccountName: naming.outputs.cosmosAccountName
    location: location
    enableFreeTier: enableFreeTier
  }
}

// ── Service Bus ───────────────────────────────────────────────────────────────

module serviceBus 'modules/service-bus.bicep' = {
  name: 'service-bus'
  scope: rg
  params: {
    namespaceName: naming.outputs.serviceBusNamespaceName
    location: location
  }
}

// ── Document Intelligence ─────────────────────────────────────────────────────

module docIntelligence 'modules/document-intelligence.bicep' = {
  name: 'document-intelligence'
  scope: rg
  params: {
    accountName: naming.outputs.documentIntelligenceName
    location: location
  }
}

// ── Key Vault ─────────────────────────────────────────────────────────────────

module keyVault 'modules/key-vault.bicep' = {
  name: 'key-vault'
  scope: rg
  params: {
    keyVaultName: naming.outputs.keyVaultName
    location: location
  }
}

// ── Container Registry ────────────────────────────────────────────────────────

module acr 'modules/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    registryName: naming.outputs.containerRegistryName
    location: location
  }
}

// ── Managed Identities + Role Assignments ─────────────────────────────────────
// Must come after all resources so dependsOn can reference them.

module identity 'modules/identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    apiIdentityName: naming.outputs.apiIdentityName
    workerIdentityName: naming.outputs.workerIdentityName
    location: location
    cosmosAccountName: naming.outputs.cosmosAccountName
    storageAccountName: naming.outputs.storageAccountName
    serviceBusNamespaceName: naming.outputs.serviceBusNamespaceName
    keyVaultName: naming.outputs.keyVaultName
    docIntelligenceName: naming.outputs.documentIntelligenceName
    appInsightsName: naming.outputs.appInsightsName
  }
  dependsOn: [cosmos, storage, serviceBus, keyVault, docIntelligence, monitoring]
}

// ── Container Apps Environment ────────────────────────────────────────────────

module cae 'modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    envName: naming.outputs.containerAppsEnvName
    location: caLocation
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    logAnalyticsSharedKey: monitoring.outputs.logAnalyticsSharedKey
    existingCae: existingCae
  }
}

// ── Container App API (hello-world placeholder) ───────────────────────────────

module caApi 'modules/container-app-api.bicep' = {
  name: 'container-app-api'
  scope: rg
  params: {
    appName: naming.outputs.containerAppApiName
    location: caLocation
    containerAppsEnvId: cae.outputs.containerAppsEnvId
    apiIdentityId: identity.outputs.apiIdentityId
    apiIdentityClientId: identity.outputs.apiIdentityClientId
    keyVaultName: naming.outputs.keyVaultName
  }
  dependsOn: [keyVault]
}
