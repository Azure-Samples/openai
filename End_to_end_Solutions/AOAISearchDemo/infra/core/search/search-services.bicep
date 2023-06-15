param name string
param searchIndexName string
param location string = resourceGroup().location
param tags object = {}

param sku object = {
  name: 'standard'
}

param authOptions object = {}
param semanticSearch string = 'disabled'

@description('Key Vault ID')
param keyVaultName string = ''

@description('Key Vault ID')
param addKeysToVault bool = false

resource search 'Microsoft.Search/searchServices@2021-04-01-preview' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: authOptions
    disableLocalAuth: false
    disabledDataExfiltrationOptions: []
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    hostingMode: 'default'
    networkRuleSet: {
      bypass: 'None'
      ipRules: []
    }
    partitionCount: 1
    publicNetworkAccess: 'Enabled'
    replicaCount: 1
    semanticSearch: semanticSearch
  }
  sku: sku
}

module azureSearchService '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-SEARCH-SERVICE'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-SEARCH-SERVICE'
    secretValue: search.name
  }
}

module azureSearchKey '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-SEARCH-KEY'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-SEARCH-KEY'
    secretValue: search.listQueryKeys().value[0].key
  }
}

module azureSearchIndex '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-SEARCH-INDEX'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-SEARCH-INDEX'
    secretValue: searchIndexName
  }
}

output id string = search.id
output endpoint string = 'https://${name}.search.windows.net/'
output name string = search.name
