targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param appServicePlanName string = ''
param backendServiceName string = ''
param dataServiceName string = ''
param resourceGroupName string = ''

param searchServiceName string = ''
param searchServiceResourceGroupName string = ''
param searchServiceResourceGroupLocation string = location

param searchServiceSkuName string = 'standard'
param searchIndexName string = 'gptkbindex'

param storageAccountName string = ''
param storageResourceGroupName string = ''
param storageResourceGroupLocation string = location
param storageContainerName string = 'content'

param openAiServiceName string = ''
param openAiResourceGroupName string = ''
param openAiResourceGroupLocation string = location

param openAiSkuName string = 'S0'

param cosmosAccountName string = ''
param cosmosDatabaseName string = 'aoai-search-demo-cosmos-db'
param cosmosChatSessionsContainerName string = 'chat_sessions'
param cosmosEntitiesContainerName string = 'entities'
param cosmosPermissionsContainerName string = 'permissions'
param cosmosResourceGroupName string = ''

param appInsightsName string = ''
param appInsightsResourceGroupName string = ''
param logAnalyticsWorkspaceName string = ''

param sqlServerName string = ''
param sqlDatabaseName string = ''
param sqlResourceGroupName string = ''

param formRecognizerServiceName string = ''
param formRecognizerResourceGroupName string = ''
param formRecognizerResourceGroupLocation string = location

param formRecognizerSkuName string = 'S0'

param gptDeploymentName string = 'gpt-4'
param gptModelName string = 'gpt-4'
param classifierGptDeploymentName string = 'curie'
param classifierGptModelName string = 'text-curie-001'

@description('Id of the user or app to assign application roles')
param principalId string = ''

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(openAiResourceGroupName)) {
  name: !empty(openAiResourceGroupName) ? openAiResourceGroupName : resourceGroup.name
}

resource formRecognizerResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(formRecognizerResourceGroupName)) {
  name: !empty(formRecognizerResourceGroupName) ? formRecognizerResourceGroupName : resourceGroup.name
}

resource searchServiceResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(searchServiceResourceGroupName)) {
  name: !empty(searchServiceResourceGroupName) ? searchServiceResourceGroupName : resourceGroup.name
}

resource storageResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(storageResourceGroupName)) {
  name: !empty(storageResourceGroupName) ? storageResourceGroupName : resourceGroup.name
}

resource cosmosResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(cosmosResourceGroupName)) {
  name: !empty(cosmosResourceGroupName) ? cosmosResourceGroupName : resourceGroup.name
}

resource appInsightsResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(appInsightsResourceGroupName)) {
  name: !empty(appInsightsResourceGroupName) ? appInsightsResourceGroupName : resourceGroup.name
}

resource sqlResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(sqlResourceGroupName)) {
  name: !empty(sqlResourceGroupName) ? sqlResourceGroupName : resourceGroup.name
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      capacity: 1
    }
    kind: 'linux'
  }
}

// Keyvault to store secrets
module keyVault 'core/keyvault/keyvault.bicep' = {
  name: 'keyVault'
  scope: resourceGroup
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
  }
}


// The application frontend
module backend 'core/host/appservice.bicep' = {
  name: 'web'
  scope: resourceGroup
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.10'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    appSettings: {
      KEYVAULT_URI: keyVault.outputs.vaultUri
    }
  }
}

// Application data service
module dataService 'core/host/appservice.bicep' = {
  name: 'data-service'
  scope: resourceGroup
  params: {
    name: !empty(dataServiceName) ? dataServiceName : '${abbrs.webSitesAppService}data-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'data' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.10'
    managedIdentity: true
    appSettings: {
      KEYVAULT_URI: keyVault.outputs.vaultUri
    }
  }
}

module openAi 'core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: openAiResourceGroupLocation
    tags: tags
    sku: {
      name: openAiSkuName
    }
    deployments: [
      /* 
      NOTE: Uncomment if you want to deploy OpenAI models from scratch
      {
        name: gptDeploymentName
        model: {
          format: 'OpenAI'
          name: gptModelName
          version: '1'
        }
        scaleSettings: {
          scaleType: 'Standard'
        }
      }

      {
        name: classifierGptDeploymentName
        model: {
          format: 'OpenAI'
          name: classifierGptModelName
          version: '1'
        }
        scaleSettings: {
          scaleType: 'Standard'
        }
      }
      */
    ]
  }
}

module formRecognizer 'core/ai/cognitiveservices.bicep' = {
  name: 'formrecognizer'
  scope: formRecognizerResourceGroup
  params: {
    name: !empty(formRecognizerServiceName) ? formRecognizerServiceName : '${abbrs.cognitiveServicesFormRecognizer}${resourceToken}'
    kind: 'FormRecognizer'
    location: formRecognizerResourceGroupLocation
    tags: tags
    sku: {
      name: formRecognizerSkuName
    }
  }
}

module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  scope: searchServiceResourceGroup
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'gptkb-${resourceToken}'
    searchIndexName: searchIndexName
    location: searchServiceResourceGroupLocation
    tags: tags
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: 'free'
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
  dependsOn: [
    keyVault
  ]
}

module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: storageResourceGroup
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: 'Enabled'
    sku: {
      name: 'Standard_ZRS'
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: storageContainerName
        publicAccess: 'None'
      }
    ]
    storageContainerName: storageContainerName
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
  dependsOn: [
    keyVault
  ]
}

// Cosmos DB Deployment
module cosmosAccount 'core/database/cosmos-database.bicep' = {
  name: 'cosmos-db'
  scope: cosmosResourceGroup
  params: {
    cosmosAccountName: !empty(cosmosAccountName) ? cosmosAccountName : '${abbrs.cosmosNoSQLDBDatabaseAccounts}${resourceToken}'
    cosmosDatabaseName: !empty(cosmosDatabaseName) ? cosmosDatabaseName : '${abbrs.cosmosDatabase}${resourceToken}'
    cosmosChatSessionsContainerName: cosmosChatSessionsContainerName
    cosmosEntitiesContainerName: cosmosEntitiesContainerName
    cosmosPermissionsContainerName: cosmosPermissionsContainerName
    location: location
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
  dependsOn: [
    keyVault
  ]
}

// App Insights Deployment 
module appInsights 'core/logging/appinsights.bicep' = {
  name: 'app-insights'
  scope: appInsightsResourceGroup
  params: {
    applicationInsightsName : !empty(appInsightsName) ? appInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    logAnalyticsWorkspaceName: !empty(logAnalyticsWorkspaceName) ? logAnalyticsWorkspaceName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
  dependsOn: [
    keyVault
  ]
}

// SQL Server and Database Deployment
module sql 'core/database/sql-database.bicep' = {
  name: 'sql'
  scope: sqlResourceGroup
  params: {
    sqlServerName: !empty(sqlServerName) ? sqlServerName : '${abbrs.sqlServers}${resourceToken}'
    sqlDatabaseName: !empty(sqlDatabaseName) ? sqlDatabaseName : '${abbrs.sqlServersDatabases}${resourceToken}'
    location: location
    keyVaultName: keyVault.outputs.name
    addKeysToVault: true
  }
  dependsOn: [
    keyVault
  ]
}

// USER ROLES
module openAiRoleUser 'core/security/role.bicep' = {
  scope: openAiResourceGroup
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'User'
  }
}

module formRecognizerRoleUser 'core/security/role.bicep' = {
  scope: formRecognizerResourceGroup
  name: 'formrecognizer-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'User'
  }
}

module storageRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'User'
  }
}

module storageContribRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-contribrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'User'
  }
}

module searchRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'User'
  }
}

module searchContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'User'
  }
}

// SYSTEM IDENTITIES
module openAiRoleBackend 'core/security/role.bicep' = {
  scope: openAiResourceGroup
  name: 'openai-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleBackend 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module searchRoleBackend 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

// Adding keys to keyvault. Todo: Move openAI and formRecognizer secrets to their own biceps. 
module azureOpenAIService 'core/keyvault/keyvault_secret.bicep' = {
  name: 'AZURE_OPENAI_SERVICE'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-SERVICE'
    secretValue: openAi.outputs.name
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIGPTDeployment 'core/keyvault/keyvault_secret.bicep' = {
  name: 'AZURE_OPENAI_GPT_DEPLOYMENT'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-GPT-DEPLOYMENT'
    secretValue: gptDeploymentName
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIChatGPTDeployment 'core/keyvault/keyvault_secret.bicep' = {
  name: 'AZURE_OPENAI_CHATGPT_DEPLOYMENT'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-CHATGPT-DEPLOYMENT'
    secretValue: gptDeploymentName
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIAPIKey 'core/keyvault/keyvault_secret.bicep' = {
  name: 'AZURE_OPENAI_API_KEY'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-API-KEY'
    secretValue: openAi.outputs.apiKey
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureFormRecognizerService 'core/keyvault/keyvault_secret.bicep' = {
  name: 'AZURE_FORMRECOGNIZER_SERVICE'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-FORMRECOGNIZER-SERVICE'
    secretValue: formRecognizer.outputs.name
  }
  dependsOn: [
    keyVault
    formRecognizer
  ]
}

module azureFormRecognizerKey 'core/keyvault/keyvault_secret.bicep' = {
  name: 'AZURE_FORMRECOGNIZER_KEY'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-FORMRECOGNIZER-KEY'
    secretValue: formRecognizer.outputs.apiKey
  }
  dependsOn: [
    keyVault
    formRecognizer
  ]
}

output KEYVAULT_URI string = keyVault.outputs.vaultUri

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name

output AZURE_OPENAI_SERVICE string = openAi.outputs.name
output AZURE_OPENAI_RESOURCE_GROUP string = openAiResourceGroup.name
output AZURE_OPENAI_GPT_DEPLOYMENT string = gptDeploymentName

output AZURE_FORMRECOGNIZER_SERVICE string = formRecognizer.outputs.name
output AZURE_FORMRECOGNIZER_RESOURCE_GROUP string = formRecognizerResourceGroup.name

output AZURE_SEARCH_INDEX string = searchIndexName
output AZURE_SEARCH_SERVICE string = searchService.outputs.name
output AZURE_SEARCH_SERVICE_RESOURCE_GROUP string = searchServiceResourceGroup.name

output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_CONTAINER string = storageContainerName
output AZURE_STORAGE_RESOURCE_GROUP string = storageResourceGroup.name

output BACKEND_URI string = backend.outputs.uri

output AZURE_COSMOS_ENDPOINT string = cosmosAccount.outputs.cosmosEndpoint
output AZURE_COSMOS_KEY string = cosmosAccount.outputs.cosmosKey
output AZURE_COSMOS_DB_NAME string = cosmosDatabaseName
output AZURE_COSMOS_DB_ENTITIES_CONTAINER_NAME string = cosmosEntitiesContainerName
output AZURE_COSMOS_DB_PERMISSIONS_CONTAINER_NAME string = cosmosPermissionsContainerName
output AZURE_COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME string = cosmosChatSessionsContainerName
