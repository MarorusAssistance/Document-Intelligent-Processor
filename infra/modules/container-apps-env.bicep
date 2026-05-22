param envName string
param location string
param logAnalyticsWorkspaceId string
@secure()
param logAnalyticsSharedKey string

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
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

output containerAppsEnvId string = cae.id
output containerAppsEnvName string = cae.name
