param accountName string
param location string

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: accountName
  location: location
  kind: 'FormRecognizer'
  sku: { name: 'F0' } // 500 pages/month free
  properties: {
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true // managed identity only (M6: restrict to private endpoint)
    customSubDomainName: accountName
  }
}

output documentIntelligenceId string = documentIntelligence.id
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
