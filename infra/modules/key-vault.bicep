param keyVaultName string
param location string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true // RBAC mode — no access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false // dev: allow purge
    networkAcls: {
      defaultAction: 'Allow' // M6: restrict + private endpoint
      bypass: 'AzureServices'
    }
  }
}

// Dummy secret to validate KV access from Container App (AC-14)
resource testSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'test-secret'
  properties: {
    value: 'placeholder-replace-in-production'
    attributes: { enabled: true }
  }
}

output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
