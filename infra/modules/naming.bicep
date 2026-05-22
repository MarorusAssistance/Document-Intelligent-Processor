@description('Base name for all resources (e.g. docproc)')
param baseName string

@description('Environment abbreviation (e.g. dev, prod)')
param env string

@description('Region abbreviation (e.g. weu)')
param region string

var base = '${baseName}-${env}-${region}'
var baseNoHyphens = replace(replace(replace(base, '-', ''), '_', ''), ' ', '')

output resourceGroupName string = 'rg-${base}'
// Storage: no hyphens, max 24 chars — 'st' + 'docprocdevweu' + '001' = 18 chars
output storageAccountName string = 'st${baseNoHyphens}001'
output cosmosAccountName string = 'cosno-${base}'
output serviceBusNamespaceName string = 'sb-${base}'
output documentIntelligenceName string = 'cog-${base}'
output keyVaultName string = 'kv-${base}'
output containerAppsEnvName string = 'cae-${base}'
output containerAppApiName string = 'ca-${baseName}-api-${env}-${region}'
// ACR: no hyphens, max 50 chars — 'cr' + 'docprocdevweu' = 15 chars
output containerRegistryName string = 'cr${baseNoHyphens}'
output appInsightsName string = 'appi-${base}'
output logAnalyticsName string = 'log-${base}'
output apiIdentityName string = 'id-${baseName}-api-${env}-${region}'
output workerIdentityName string = 'id-${baseName}-worker-${env}-${region}'
