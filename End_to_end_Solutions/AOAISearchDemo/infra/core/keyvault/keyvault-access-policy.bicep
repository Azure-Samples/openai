param keyVaultName string
param accessPolicies array = []

resource symbolicname 'Microsoft.KeyVault/vaults/accessPolicies@2022-07-01' = {
  name: 'replace'
  parent: keyVault
  properties: {
    accessPolicies: accessPolicies
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' existing = if (!(empty(keyVaultName))) {
  name: keyVaultName
}

