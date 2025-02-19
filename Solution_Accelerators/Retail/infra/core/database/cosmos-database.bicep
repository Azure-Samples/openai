// cosmos-database.bicep
targetScope = 'resourceGroup'

@description('Name of Cosmos DB Account')
param cosmosAccountName string

@description('Key Vault Name')
param keyVaultName string = ''

@description('Add keys to Key Vault')
param addKeysToVault bool = false

@description('Location for the resources')
param location string = resourceGroup().location

@description('Name of the Cosmos DB Database')
param cosmosDatabaseName string

@description('Name of the Chat Sessions Container')
param cosmosChatSessionsContainerName string

@description('Name of the Entities Container')
param cosmosEntitiesContainerName string

@description('Tags to apply to resources')
param tags object = {}

@description('Set to true to create a Private Endpoint')
param createPrivateEndpoint bool = false

@description('Name of the Private Endpoint')
param privateEndpointName string = '${cosmosAccountName}-pe'

@description('Resource Group Name of the Virtual Network')
param virtualNetworkResourceGroupName string = resourceGroup().name

@description('Name of the Virtual Network')
param virtualNetworkName string

@description('Name of the Subnet')
param subnetName string

@description('Name of the Private DNS Zone')
param privateDnsZoneName string = 'privatelink.documents.azure.com'

// Cosmos DB Account
resource account 'Microsoft.DocumentDB/databaseAccounts@2022-05-15' = {
  name: toLower(cosmosAccountName)
  location: location
  tags: tags
  properties: {
    enableFreeTier: false
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
      }
    ]
    disableLocalAuth: true
  }
}

// Cosmos Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2022-05-15' = {
  parent: account
  name: cosmosDatabaseName
  properties: {
    resource: {
      id: cosmosDatabaseName
    }
    options: {
      throughput: 400
    }
  }
}

// Chat Sessions Container
resource cosmosChatSessionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2022-05-15' = {
  parent: database
  name: cosmosChatSessionsContainerName
  properties: {
    resource: {
      id: cosmosChatSessionsContainerName
      partitionKey: {
        paths: [
          '/partition_key'
        ]
        kind: 'Hash'
      }
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: [
              '/partition_key'
            ]
          }
        ]
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/_etag/?'
          }
        ]
      }
    }
  }
}

// Private DNS Zone for the endpoint
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (createPrivateEndpoint) {
  name: privateDnsZoneName
  location: 'global'
  tags: tags
}

// **Added: Link the Private DNS Zone to your Virtual Network**
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
  dependsOn: [
    privateDnsZone
  ]
}

// Private Endpoint for Cosmos DB
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2021-08-01' = if (createPrivateEndpoint) {
  name: privateEndpointName
  location: location
  properties: {
    subnet: {
      id: resourceId(virtualNetworkResourceGroupName, 'Microsoft.Network/virtualNetworks/subnets', virtualNetworkName, subnetName)
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointName}-cosmosConnection'
        properties: {
          privateLinkServiceId: account.id
          groupIds: [
            'Sql' // Change this if using a different API
          ]
          requestMessage: 'PE for Cosmos DB'
        }
      }
    ]
  }
  dependsOn: [
    privateDnsZoneVNetLink // **Ensure the VNet Link is created before the Private Endpoint**
  ]
}

// Private DNS Zone Group to link DNS zone with the private endpoint
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-02-01' = if (createPrivateEndpoint) {
  name: 'default' // **Using 'default' as the standard name**
  parent: privateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
  dependsOn: [
    privateEndpoint
    privateDnsZone
  ]
}

// Modules for Key Vault secrets
module azureCosmosKeySecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'cosmos-key'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-KEY'
    secretValue: account.listKeys().primaryMasterKey
  }
}

module azureCosmosEndpointSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'cosmos-endpoint'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-ENDPOINT'
    secretValue: account.properties.documentEndpoint
  }
}

module azureCosmosDbNameSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'cosmos-db-name'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-NAME'
    secretValue: cosmosDatabaseName
  }
}

module azureCosmosDbChatSessionsContainerNameSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'cosmos-chat-sessions-container-name'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-CHAT-SESSIONS-CONTAINER-NAME'
    secretValue: cosmosChatSessionsContainerName
  }
}

module azureCosmosDbEntitiesContainerNameSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'cosmos-entities-container-name'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-ENTITIES-CONTAINER-NAME'
    secretValue: cosmosEntitiesContainerName
  }
}
