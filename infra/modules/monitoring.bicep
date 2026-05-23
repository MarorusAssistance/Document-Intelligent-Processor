param logAnalyticsName string
param appInsightsName string
param location string

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
  }
}

output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
// Required by Container Apps Environment for log streaming
#disable-next-line outputs-should-not-contain-secrets
output logAnalyticsSharedKey string = logAnalytics.listKeys().primarySharedKey
output logAnalyticsResourceId string = logAnalytics.id
output appInsightsId string = appInsights.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
