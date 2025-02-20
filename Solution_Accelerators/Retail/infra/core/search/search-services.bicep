param name string
param searchIndexName string
param location string = resourceGroup().location
param tags object = {}

param sku object = {
  name: 'standard'
}

// param authOptions object = {}
// param semanticSearch string = 'disabled'

param kbFieldsContent string
param kbFieldsCategory string
param kbFieldsSourcePage string
param skipVectorization bool = false

@description('Key Vault ID')
param keyVaultName string = ''

@description('Add keys to Key Vault')
param addKeysToVault bool = false

param createPrivateEndpoint bool = false
param privateEndpointName string = '${name}-pe'
param virtualNetworkResourceGroupName string = resourceGroup().name
param virtualNetworkName string
param subnetName string
param privateDnsZoneName string = 'privatelink.search.windows.net'

resource search 'Microsoft.Search/searchServices@2022-09-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: null
    disableLocalAuth: true
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    hostingMode: 'default'
    networkRuleSet: {
      // bypass: 'None'
      ipRules: []
    }
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    replicaCount: 1
    // semanticSearch: semanticSearch
  }
  sku: sku
}

// Private Endpoint for Search Service
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2021-08-01' = if (createPrivateEndpoint) {
  name: privateEndpointName
  location: location
  properties: {
    subnet: {
      id: resourceId(virtualNetworkResourceGroupName, 'Microsoft.Network/virtualNetworks/subnets', virtualNetworkName, subnetName)
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointName}-searchServiceConnection'
        properties: {
          privateLinkServiceId: search.id
          groupIds: [
            'searchService'
          ]
          requestMessage: 'Please approve the connection.'
        }
      }
    ]
  }
}

// Private DNS Zone for the endpoint
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneName
  location: 'global'
}

resource privateDnsZoneVNetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (createPrivateEndpoint) {
  parent: privateDnsZone
  name: '${virtualNetworkName}-vnetLink'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: resourceId(virtualNetworkResourceGroupName, 'Microsoft.Network/virtualNetworks', virtualNetworkName)
    }
    registrationEnabled: false
  }
}

// Private DNS Zone Group to link DNS zone with the private endpoint
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-02-01' = {
  name: '${privateEndpointName}-dnsZoneGroup'
  parent: privateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'default'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
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

module skipVectorizationSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'skipVectorization'
  params: {
    keyVaultName: keyVaultName
    secretName: 'SEARCH-SKIP-VECTORIZATION'
    secretValue: skipVectorization ? 'true' : 'false'
  }
}

output id string = search.id
output endpoint string = 'https://${name}.search.windows.net/'
output name string = search.name
