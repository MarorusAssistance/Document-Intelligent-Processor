targetScope = 'subscription'

@description('Base name for all resources (e.g. docproc)')
param baseName string

@description('Environment abbreviation (e.g. dev, prod)')
param env string

@description('Region abbreviation (e.g. weu)')
param region string

var base = '${baseName}-${env}-${region}'
var baseNoHyphens = replace(replace(replace(base, '-', ''), '_', ''), ' ', '')
// 4-char deterministic suffix derived from subscription ID — prevents global name collisions
var uniqueSuffix = substring(uniqueString(subscription().subscriptionId), 0, 4)

output resourceGroupName string = 'rg-${base}'
// Storage: no hyphens, max 24 chars — 'st' + 'docprocdevweu' + '001' = 18 chars
output storageAccountName string = 'st${baseNoHyphens}001'
output cosmosAccountName string = 'cosno-${base}'
// Service Bus: globally unique name — append subscription-derived suffix
output serviceBusNamespaceName string = 'sb-${base}-${uniqueSuffix}'
output documentIntelligenceName string = 'cog-${base}'
// Key Vault: globally unique, max 24 chars — 'kv-docproc-dev-weu-xxxx' = 23 chars
output keyVaultName string = 'kv-${base}-${uniqueSuffix}'
output containerAppsEnvName string = 'cae-${base}'
output containerAppApiName string = 'ca-${baseName}-api-${env}-${region}'
// ACR: no hyphens, max 50 chars — 'cr' + 'docprocdevweu' = 15 chars
output containerRegistryName string = 'cr${baseNoHyphens}'
output appInsightsName string = 'appi-${base}'
output logAnalyticsName string = 'log-${base}'
output apiIdentityName string = 'id-${baseName}-api-${env}-${region}'
output workerIdentityName string = 'id-${baseName}-worker-${env}-${region}'
