param namespaceName string
param location string

resource namespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: namespaceName
  location: location
  sku: { name: 'Basic', tier: 'Basic' }
  properties: {
    minimumTlsVersion: '1.2'
    disableLocalAuth: true // managed identity only
  }
}

resource ocrQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: namespace
  name: 'ocr-extraction-jobs'
  properties: {
    lockDuration: 'PT5M'
    maxDeliveryCount: 5
    deadLetteringOnMessageExpiration: true
    defaultMessageTimeToLive: 'P1D'
  }
}

output serviceBusNamespaceId string = namespace.id
output serviceBusNamespaceName string = namespace.name
output serviceBusEndpoint string = namespace.properties.serviceBusEndpoint
