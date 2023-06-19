param name string
param location string = resourceGroup().location
param tags object = {}
param sku object = {
  family: 'A'
  name: 'standard'
}
param enabledForDeployment bool = false
param enabledForDiskEncryption bool = false
param enabledForTemplateDeployment bool = false

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: sku
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: enabledForDeployment
    enabledForDiskEncryption: enabledForDiskEncryption
    enabledForTemplateDeployment: enabledForTemplateDeployment
  }
}

output id string = keyVault.id
output name string = keyVault.name
output vaultUri string = 'https://${keyVault.name}.vault.azure.net/'
