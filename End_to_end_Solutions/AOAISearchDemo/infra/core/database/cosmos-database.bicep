// Usage (sh):
// > az login
// > az account set --name <subscription name>
// > az group create --name <resource group name> --location <region>
// > az deployment group create --template-file .\src\deployment\cosmos_deploy.bicep --resource-group <resource group name> --parameters cosmosAccountName="aoai-demo-db"
//  


targetScope = 'resourceGroup'

@description('Name of Cosmos DB Account')
param cosmosAccountName string

@description('Key Vault ID')
param keyVaultName string = ''

@description('Key Vault ID')
param addKeysToVault bool = false

param location string = resourceGroup().location

param cosmosDatabaseName string

param cosmosChatSessionsContainerName string

param cosmosEntitiesContainerName string

param cosmosPermissionsContainerName string

// Cosmos Account

resource account 'Microsoft.DocumentDB/databaseAccounts@2022-05-15' = {
  name: toLower(cosmosAccountName)
  location: location
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

// Entities Container

resource cosmosEntitiesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2022-05-15' = {
  parent: database
  name: cosmosEntitiesContainerName
  properties: {
    resource: {
      id: cosmosEntitiesContainerName
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
              '/user_id', '/group_id', '/resource_id'
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

// Permissions Container

resource cosmosPermissionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2022-05-15' = {
  parent: database
  name: cosmosPermissionsContainerName
  properties: {
    resource: {
      id: cosmosPermissionsContainerName
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
              '/rule_id'
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

module azureCosmosKeySecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-COSMOS-KEY'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-KEY'
    secretValue: account.listKeys().primaryMasterKey
  }
}

module azureCosmosDbNameSecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-COSMOS-DB-NAME'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-NAME'
    secretValue: cosmosDatabaseName
  }
}

module azureCosmosDbChatSessionsContainerNameSecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-COSMOS-DB-CHAT-SESSIONS-CONTAINER-NAME'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-CHAT-SESSIONS-CONTAINER-NAME'
    secretValue: cosmosChatSessionsContainerName
  }
}

module azureCosmosDbEntitiesContainerNameSecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-COSMOS-DB-ENTITIES-CONTAINER-NAME'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-ENTITIES-CONTAINER-NAME'
    secretValue: cosmosEntitiesContainerName
  }
}

module azureCosmosDbPermissionsContainerNameSecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'AZURE-COSMOS-DB-PERMISSIONS-CONTAINER-NAME'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-PERMISSIONS-CONTAINER-NAME'
    secretValue: cosmosPermissionsContainerName
  }
}

output cosmosAccountID string = account.id

output cosmosKey string = account.listKeys().primaryMasterKey

output cosmosEndpoint string = account.properties.documentEndpoint
