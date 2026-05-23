param cosmosAccountName string
param location string

@description('Enable free tier (only one per subscription). Falls back to serverless if false.')
param enableFreeTier bool = true

var capabilities = enableFreeTier
  ? []
  : [{ name: 'EnableServerless' }]

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: enableFreeTier
    capabilities: capabilities
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: { tier: 'Continuous7Days' }
    }
    disableLocalAuth: true // force managed identity; no keys
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'docproc'
  properties: {
    resource: { id: 'docproc' }
    // Shared throughput only valid on provisioned (non-serverless) accounts with free tier
    options: enableFreeTier ? { throughput: 1000 } : {}
  }
}

resource documentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'documents'
  properties: {
    resource: {
      id: 'documents'
      partitionKey: {
        paths: ['/clientId']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [{ path: '/*' }]
        excludedPaths: [{ path: '/"_etag"/?' }]
      }
    }
  }
}

resource jobsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'jobs'
  properties: {
    resource: {
      id: 'jobs'
      partitionKey: {
        paths: ['/clientId']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [{ path: '/*' }]
        excludedPaths: [{ path: '/"_etag"/?' }]
      }
    }
  }
}

output cosmosAccountId string = cosmosAccount.id
output cosmosAccountName string = cosmosAccount.name
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
