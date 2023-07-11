param name string
param searchIndexName string
param location string = resourceGroup().location
param tags object = {}

param sku object = {
  name: 'standard'
}

param authOptions object = {}
param semanticSearch string = 'disabled'

param kbFieldsContent string
param kbFieldsCategory string
param kbFieldsSourcePage string

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

module azureSearchService '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-search-service'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-SEARCH-SERVICE'
    secretValue: search.name
  }
}

module azureSearchKey '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-search-key'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-SEARCH-KEY'
    secretValue: search.listQueryKeys().value[0].key
  }
}

module azureSearchIndex '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-search-index'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-SEARCH-INDEX'
    secretValue: searchIndexName
  }
}

module kbFieldsContentSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'kb-fields-content'
  params: {
    keyVaultName: keyVaultName
    secretName: 'KB-FIELDS-CONTENT'
    secretValue: kbFieldsContent
  }
}

module kbFieldsCategorySecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'kb-fields-category'
  params: {
    keyVaultName: keyVaultName
    secretName: 'KB-FIELDS-CATEGORY'
    secretValue: kbFieldsCategory
  }
}

module kbFieldsSourcePageSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'kb-fields-sourcepage'
  params: {
    keyVaultName: keyVaultName
    secretName: 'KB-FIELDS-SOURCEPAGE'
    secretValue: kbFieldsSourcePage
  }
}

output id string = search.id
output endpoint string = 'https://${name}.search.windows.net/'
output name string = search.name
