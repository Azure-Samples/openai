param name string
param storageContainerName string
param storageImageContainerName string
param location string = resourceGroup().location
param tags object = {}

@allowed([ 'Hot', 'Cool', 'Premium' ])
param accessTier string = 'Hot'
param allowBlobPublicAccess bool = false
param allowCrossTenantReplication bool = true
param allowSharedKeyAccess bool = false
param defaultToOAuthAuthentication bool = false
param deleteRetentionPolicy object = {}
@allowed([ 'AzureDnsZone', 'Standard' ])
param dnsEndpointType string = 'Standard'
param kind string = 'StorageV2'
param minimumTlsVersion string = 'TLS1_2'
@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Disabled'
param sku object = { name: 'Standard_LRS' }

param containers array = []

// Key Vault
param keyVaultName string = ''
param addKeysToVault bool = false

// Private Endpoint
param createPrivateEndpoint bool = false
param privateEndpointName string = '${name}-pe'
param virtualNetworkResourceGroupName string = resourceGroup().name
param virtualNetworkName string
param subnetName string
// param privateDnsZoneName string = 'privatelink.${environment().suffixes.storage}'
param privateDnsZoneName string = 'privatelink.blob.core.windows.net'

resource storage 'Microsoft.Storage/storageAccounts@2022-05-01' = {
  name: name
  location: location
  tags: tags
  kind: kind
  sku: sku
  properties: {
    accessTier: accessTier
    allowBlobPublicAccess: allowBlobPublicAccess
    allowCrossTenantReplication: allowCrossTenantReplication
    allowSharedKeyAccess: allowSharedKeyAccess
    defaultToOAuthAuthentication: defaultToOAuthAuthentication
    dnsEndpointType: dnsEndpointType
    minimumTlsVersion: minimumTlsVersion
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    publicNetworkAccess: publicNetworkAccess
  }

  resource blobServices 'blobServices' = if (!empty(containers)) {
    name: 'default'
    properties: {
      deleteRetentionPolicy: deleteRetentionPolicy
    }
    resource container 'containers' = [for container in containers: {
      name: container.name
      properties: {
        publicAccess: container.?publicAccess ?? 'None'
      }
    }]
  }
}

// Private Endpoint for Blob Storage
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2021-08-01' = if (createPrivateEndpoint) {
  name: privateEndpointName
  location: location
  properties: {
    subnet: {
      id: resourceId(virtualNetworkResourceGroupName, 'Microsoft.Network/virtualNetworks/subnets', virtualNetworkName, subnetName)
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointName}-storageConnection'
        properties: {
          privateLinkServiceId: storage.id
          groupIds: [
            'blob' // Change this if using a different API
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


module azureStorageAccount '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-storage-account'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-STORAGE-ACCOUNT'
    secretValue: storage.name
  }
}

module azureStorageContainer '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-storage-container'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-STORAGE-CONTAINER'
    secretValue: storageContainerName
  }
}


module azureImageContainer '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-image-container'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-STORAGE-IMAGE-CONTAINER'
    secretValue: storageImageContainerName
  }
}

module azureBlobConnectionString '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-blob-connection-string'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-BLOB-CONNECTION-STRING'
    secretValue: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
  }
}

output name string = storage.name
output primaryEndpoints object = storage.properties.primaryEndpoints
