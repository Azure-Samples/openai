param name string
param storageContainerName string
param location string = resourceGroup().location
param tags object = {}

@allowed([ 'Hot', 'Cool', 'Premium' ])
param accessTier string = 'Hot'
param allowBlobPublicAccess bool = false
param allowCrossTenantReplication bool = true
param allowSharedKeyAccess bool = true
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

@description('Key Vault ID')
param keyVaultName string = ''

@description('Key Vault ID')
param addKeysToVault bool = false

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
        publicAccess: contains(container, 'publicAccess') ? container.publicAccess : 'None'
      }
    }]
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

module azureBlobConnectionString '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'azure-blob-connection-string'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-BLOB-CONNECTION-STRING'
    secretValue: concat('DefaultEndpointsProtocol=https;AccountName=${storage.name};',
    'AccountKey=${listKeys(storage.id, storage.apiVersion).keys[0].value};',
    'EndpointSuffix=${environment().suffixes.storage}')
  }
}

output name string = storage.name
output primaryEndpoints object = storage.properties.primaryEndpoints
