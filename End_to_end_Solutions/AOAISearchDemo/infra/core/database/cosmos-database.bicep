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

param principalId string

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

// Account roles

resource sqlRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2023-04-15' = {
  parent: account
  name: guid('sql-role-definition-', principalId, account.id)
  properties: {
    roleName: 'Cosmos DB metadata reader and container creator role'
    type: 'CustomRole'
    assignableScopes: [
      account.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/create'
        ]
      }
    ]
  }
}

resource sqlRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-04-15' = {
  parent: account
  name: guid('sql-role-definition-', principalId, account.id)
  properties: {
    roleDefinitionId: sqlRoleDefinition.id
    principalId: principalId
    scope: account.id
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

module azureCosmosDbPermissionsContainerNameSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault) {
  name: 'cosmos-permissions-container-name'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-COSMOS-DB-PERMISSIONS-CONTAINER-NAME'
    secretValue: cosmosPermissionsContainerName
  }
}
