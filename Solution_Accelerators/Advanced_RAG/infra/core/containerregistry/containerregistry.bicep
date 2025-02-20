param name string
param sku string = 'Standard'
param location string = resourceGroup().location
param tags object = {}

@description('Key Vault ID')
param keyVaultName string = ''

@description('Add keys to Key Vault')
param addKeysToVault bool = false

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: true
  }
}

module containerRegistryLoginServer '../keyvault/keyvault-secret.bicep' = if(addKeysToVault){
  name: 'containerRegistryLoginServer'
  params: {
    keyVaultName: keyVaultName
    secretName: 'CONTAINER-REGISTRY-LOGIN-SERVER'
    secretValue: containerRegistry.properties.loginServer
  }
}

output loginServer string = containerRegistry.properties.loginServer
