param appName string
param location string
param containerAppsEnvId string
param apiIdentityId string
param apiIdentityClientId string
param keyVaultName string

// Reference KV to read secret URI for the test-secret (AC-14)
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource caApi 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${apiIdentityId}': {} }
  }
  properties: {
    environmentId: containerAppsEnvId
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'http'
      }
      secrets: [
        {
          name: 'test-secret'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/test-secret'
          identity: apiIdentityId
        }
      ]
    }
    template: {
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
      containers: [
        {
          name: 'api'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: apiIdentityClientId
            }
            {
              name: 'TEST_SECRET'
              secretRef: 'test-secret'
            }
          ]
        }
      ]
    }
  }
}

output containerAppUrl string = caApi.properties.configuration.ingress.fqdn
output containerAppId string = caApi.id
