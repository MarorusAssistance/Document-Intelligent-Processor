param envName string
param location string
param logAnalyticsWorkspaceId string
@secure()
param logAnalyticsSharedKey string
@description('Skip creation and reference existing CAE (set true after first successful provision)')
param existingCae bool = false

resource caeNew 'Microsoft.App/managedEnvironments@2024-03-01' = if (!existingCae) {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspaceId
        sharedKey: logAnalyticsSharedKey
      }
    }
    zoneRedundant: false // dev: single zone
  }
}

resource caeRef 'Microsoft.App/managedEnvironments@2024-03-01' existing = if (existingCae) {
  name: envName
}

output containerAppsEnvId string = existingCae ? caeRef.id : caeNew.id
output containerAppsEnvName string = envName
