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
param searchSkipVectorization bool = false

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
param deployOpenAIModels bool = false
param gptDeploymentName string = ''
param gptModelName string = ''
param gptModelVersion string = ''
param classifierGptDeploymentName string = ''
param classifierGptModelName string = ''
param classifierGptModelVersion string = ''
param embeddingsGptDeploymentName string = ''
param embeddingsGptModelName string = ''
param embeddingsGptModelVersion string = ''
param embeddingsApiVersion string = '2023-03-15-preview'
param embeddingsTokenLimit string = ''
param embeddingsDimensions string = ''

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
    principalId: principalId
  }
}

// Application backend service
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
      ENVIRONMENT: 'PROD'
    }
    keyVaultName: keyVault.outputs.name
    applicationInsightsName: appInsights.outputs.applicationInsightsName
    appCommandLine: 'gunicorn --bind=0.0.0.0 --timeout 600 backend.app:app'
  }
  dependsOn: [
    keyVault
  ]
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
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    appSettings: {
      ENVIRONMENT: 'PROD'
    }
    keyVaultName: keyVault.outputs.name
    applicationInsightsName: appInsights.outputs.applicationInsightsName
    appCommandLine: 'gunicorn --bind=0.0.0.0 --timeout 600 data.app:app'
  }
  dependsOn: [
    keyVault
  ]
}

// Inbound access rules for data microservice
module dataServiceInboundAccessRules 'core/host/appservice-config.bicep' = {
  name: 'dataServiceInboundAccessRules'
  scope: resourceGroup
  params: {
    appServiceName: dataService.outputs.name
    allowedIpAddresses: backend.outputs.outboundIpAddresses
  }
  dependsOn: [
    backend
    dataService
  ]
}

// Keyvault access policies for the services
module servicesKeyVaultAccessPolicies 'core/keyvault/keyvault-access-policy.bicep' = {
  name: 'servicesKeyVaultAccessPolicies'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    accessPolicies: [
      {
        objectId: backend.outputs.identityPrincipalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
        tenantId: subscription().tenantId
      }
      {
        objectId: dataService.outputs.identityPrincipalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
        tenantId: subscription().tenantId
      }
    ]    
  }
  dependsOn: [
    keyVault
    backend
    dataService
  ]
}

module openAi 'core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesOpenAI}${resourceToken}'
    location: openAiResourceGroupLocation
    tags: tags
    sku: {
      name: openAiSkuName
    }
    deployments: deployOpenAIModels && !searchSkipVectorization ? [
        {
          name: !empty(gptDeploymentName) ? gptDeploymentName : 'gpt-4'
          model: {
            format: 'OpenAI'
            name: !empty(gptModelName) ? gptModelName : 'gpt-4'
            version: !empty(gptModelVersion) ? gptModelVersion : '0314'
          }
          scaleSettings: {
            scaleType: 'Standard'
          }
        }
        {
          name: !empty(classifierGptDeploymentName) ? classifierGptDeploymentName : 'gpt-35-turbo'
          model: {
            format: 'OpenAI'
            name: !empty(classifierGptModelName) ? classifierGptModelName : 'gpt-35-turbo'
            version: !empty(classifierGptModelVersion) ? classifierGptModelVersion : '0301'
          }
          scaleSettings: {
            scaleType: 'Standard'
          }
        }
        {
          name: !empty(embeddingsGptDeploymentName) ? embeddingsGptDeploymentName : 'text-embedding-ada-002'
          model: {
            format: 'OpenAI'
            name: !empty(embeddingsGptModelName) ? embeddingsGptModelName : 'text-embedding-ada-002'
            version: !empty(embeddingsGptModelVersion) ? embeddingsGptModelVersion : '2'
          }
          scaleSettings: {
            scaleType: 'Standard'
          }
        }
      ] : deployOpenAIModels ? [
        {
          name: !empty(gptDeploymentName) ? gptDeploymentName : 'gpt-4'
          model: {
            format: 'OpenAI'
            name: !empty(gptModelName) ? gptModelName : 'gpt-4'
            version: !empty(gptModelVersion) ? gptModelVersion : '0314'
          }
          scaleSettings: {
            scaleType: 'Standard'
          }
        }
        {
          name: !empty(classifierGptDeploymentName) ? classifierGptDeploymentName : 'gpt-35-turbo'
          model: {
            format: 'OpenAI'
            name: !empty(classifierGptModelName) ? classifierGptModelName : 'gpt-35-turbo'
            version: !empty(classifierGptModelVersion) ? classifierGptModelVersion : '0301'
          }
          scaleSettings: {
            scaleType: 'Standard'
          }
        }
      ] : []
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
    kbFieldsContent: 'content'
    kbFieldsCategory: 'category'
    kbFieldsSourcePage: 'sourcepage'
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
    principalId: principalId
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
    resourceGroupName: openAiResourceGroup.name
  }
}

module formRecognizerRoleUser 'core/security/role.bicep' = {
  scope: formRecognizerResourceGroup
  name: 'formrecognizer-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'User'
    resourceGroupName: formRecognizerResourceGroup.name
  }
}

module storageRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'User'
    resourceGroupName: storageResourceGroup.name
  }
}

module storageContribRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-contribrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'User'
    resourceGroupName: storageResourceGroup.name
  }
}

module searchRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'User'
    resourceGroupName: searchServiceResourceGroup.name
  }
}

module searchContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'User'
    resourceGroupName: searchServiceResourceGroup.name
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
    resourceGroupName: openAiResourceGroup.name
  }
}

module storageRoleBackend 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
    resourceGroupName: storageResourceGroup.name
  }
}

module searchRoleBackend 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
    resourceGroupName: searchServiceResourceGroup.name
  }
}

// Adding secrets to keyvault. Todo: Move openAI and formRecognizer secrets to their own biceps. 
module azureOpenAIGPTService 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-gpt-service'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-GPT4-SERVICE'
    secretValue: openAi.outputs.name
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIClassifierService 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-classifier-service'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-CLASSIFIER-SERVICE'
    secretValue: openAi.outputs.name
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIEmbeddingsService 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-embeddings-service'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-EMBEDDINGS-SERVICE'
    secretValue: openAi.outputs.name
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIGptKey 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-gpt-api-key'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-GPT4-API-KEY'
    secretValue: openAi.outputs.apiKey
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIClassifierKey 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-classifier-api-key'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-CLASSIFIER-API-KEY'
    secretValue: openAi.outputs.apiKey
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIEmbeddingsKey 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-embeddings-api-key'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-EMBEDDINGS-API-KEY'
    secretValue: openAi.outputs.apiKey
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIEmbeddingsEngineName 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-embeddings-engine-name'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-EMBEDDINGS-ENGINE-NAME'
    secretValue: embeddingsGptDeploymentName
  }
  dependsOn: [
    keyVault
    openAi
  ]
}

module azureOpenAIEmbeddingsDimensions 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-embeddings-dimensions'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-EMBEDDINGS-DIMENSIONS'
    secretValue: embeddingsDimensions
  }
  dependsOn: [
    keyVault
  ]
}

module azureOpenAIEmbeddingsTokenLimit 'core/keyvault/keyvault-secret.bicep' = {
  name: 'openai-secret-embeddings-token-limit'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AZURE-OPENAI-EMBEDDINGS-TOKEN-LIMIT'
    secretValue: embeddingsTokenLimit
  }
  dependsOn: [
    keyVault
  ]
}

module searchSkipVectorizationSecret 'core/keyvault/keyvault-secret.bicep' = {
  name: 'search-secret-skip-vectorization'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'SEARCH-SKIP-VECTORIZATION'
    secretValue: searchSkipVectorization ? 'true' : 'false'
  }
  dependsOn: [
    keyVault
  ]
}

module azureFormRecognizerService 'core/keyvault/keyvault-secret.bicep' = {
  name: 'formrecognizer-secret-service-name'
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

module azureFormRecognizerKey 'core/keyvault/keyvault-secret.bicep' = {
  name: 'formrecognizer-secret-key'
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

module azureSQLServerName 'core/keyvault/keyvault-secret.bicep' = {
  name: 'sqlserver-name'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'SQL-SERVER-NAME'
    secretValue: sql.outputs.sqlServerName
  }
  dependsOn: [
    keyVault
    sql
  ]
}

module dataServiceUri 'core/keyvault/keyvault-secret.bicep' = {
  name: 'appservice-data-service-uri'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'DATA-SERVICE-URI'
    secretValue:'https://${dataService.outputs.hostname}'
  }
  dependsOn: [
    keyVault
    dataService
  ]
}

output KEYVAULT_NAME string = keyVault.outputs.name
output AZURE_RESOURCE_GROUP string = resourceGroup.name
