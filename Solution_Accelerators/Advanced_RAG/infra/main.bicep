targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Default resource group for all resources')
param resourceGroupName string = ''

param appServicePlanName string = ''
param appServicePlanResourceLocation string = location

param frontendWebAppName string = ''

param storageAccountName string = ''
param storageResourceGroupName string = ''
param storageResourceGroupLocation string = location
param storageContainerName string = 'content'
param storageImageContainerName string = 'images'

param openAIResourceGroupName string = '' 
param openAIResourceGroupLocation string = location
param openAIResourceName string = ''
param openAiSkuName string = 'S0'
// param gpt4ServiceName string = ''
// param gpt4ResourceGroupName string = ''
// param gpt4ResourceGroupLocation string = location
// param gpt4DeploymentName string = 'gpt4-1106'

// param gpt35TurboServiceName string = ''
// param gpt35TurboResourceGroupName string = ''
// param gpt35TurboResourceGroupLocation string = location
// param gpt35TurboDeploymentName string
// param gpt35ModelVersion string

// param gpt4VServiceName string = ''
// param gpt4VResourceGroupName string = ''
// param gpt4VResourceGroupLocation string = location
// param gpt4VDeploymentName string =''

// param deployOpenAIModels bool = true
// param gptDeploymentName string = ''
// param gpt4ModelName string = ''
// param gptModelVersion string = ''
// param classifierGptDeploymentName string = ''
// param classifierGptModelName string = ''
// param classifierGptModelVersion string = ''

// param embeddingsGptDeploymentName string = ''
param embeddingsGptModelName string = ''
// param embeddingsGptModelVersion string = ''
// param embeddingsApiVersion string = '2023-03-15-preview'
param embeddingsTokenLimit string = '8191'
param embeddingsDimensions string = '1536'

param virtualNetworkName string = ''
param virtualNetworkAddressPrefix string = '10.255.0.0/16'
param subnetNames object = {
  aksSubnetName: 'aksSubnet'
  appGatewaySubnetName: 'appGatewaySubnet'
  endpointsSubnetName: 'endpointsSubnet'
}
param subnetPrefixes object = {
  aksSubnetPrefix: '10.255.1.0/24'
  endpointsSubnetPrefix: '10.255.101.0/24'
  appGatewaySubnetPrefix: '10.255.201.0/24'
}

param cosmosAccountName string = ''
param cosmosDatabaseName string = 'chat-scenario-cosmos-db'
param cosmosChatSessionsContainerName string = 'chat_sessions'
param cosmosEntitiesContainerName string = 'entities'
param cosmosResourceGroupName string = ''
param createPrivateEndpoint bool = true
param cosmosPrivateEndpointName string = ''

param appInsightsName string = ''
param appInsightsResourceGroupName string = ''
param appInsightsResourceLocation string = location
param logAnalyticsWorkspaceName string = ''

param searchServiceName string = ''
param searchServiceResourceGroupName string = ''
param searchServiceResourceGroupLocation string = location
param searchSkipVectorization bool = false
param searchServiceSkuName string = 'standard'
param searchIndexName string = 'contractindex'

param multiAccountCogServiceName string = ''
param multiAccountCogServiceResourceGroupName string = ''
param multiAccountCogServiceResourceGroupLocation string = location
param multiAccountCogServiceSkuName string = 'S0'

param contentSafetyName string = ''
param contentSafetyResourceGroupName string = ''
param contentSafetyResourceGroupLocation string = location
param contentSafetySkuName string = 'S0'

param documentIntelligenceName string = ''
param documentIntelligenceResourceGroupName string = ''
param documentIntelligenceResourceGroupLocation string = location
param documentIntelligenceSkuName string = 'S0'

param containerRegistryServiceName string = ''
param containerRegistryResourceGroupName string = ''
param containerRegistryResourceGroupLocation string = location
param containerRegistrySkuName string = 'Standard'

param keyVaultResourceLocation string = location

param appGatewayName string = 'ingress-appgateway'

param aksResourceGroupName string
param aksAgentPoolVMSize string
param aksUserPoolVMSize string
param aksVersion string
param aksClusterLocation string = location
param tag object = {}

@description('Id of the user or app to assign application roles')
param principalId string

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

var tags = union(tag, { 'azd-env-name': environmentName })

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(openAIResourceGroupName)) {
  name: !empty(openAIResourceGroupName) ? openAIResourceGroupName : resourceGroup.name
}

resource multiAccountCogServiceResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(multiAccountCogServiceResourceGroupName)) {
  name: !empty(multiAccountCogServiceResourceGroupName) ? multiAccountCogServiceResourceGroupName : resourceGroup.name
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

resource containerRegistryResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(containerRegistryResourceGroupName)) {
  name: !empty(containerRegistryResourceGroupName) ? containerRegistryResourceGroupName : resourceGroup.name
}

resource contentSafetyResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(contentSafetyResourceGroupName)) {
  name: !empty(contentSafetyResourceGroupName) ? contentSafetyResourceGroupName : resourceGroup.name
}

resource documentIntelligenceResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(contentSafetyResourceGroupName)) {
  name: !empty(documentIntelligenceResourceGroupName) ? documentIntelligenceResourceGroupName : resourceGroup.name
}

resource aksResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(aksResourceGroupName)) {
  name: !empty(aksResourceGroupName) ? aksResourceGroupName : resourceGroup.name
}

var aksClusterName = '${abbrs.containerServiceManagedClusters}${resourceToken}'

// Keyvault to store secrets
module keyVault 'core/keyvault/keyvault.bicep' = {
  name: 'keyVault'
  scope: resourceGroup
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: keyVaultResourceLocation
    createPrivateEndpoint: createPrivateEndpoint
    virtualNetworkResourceGroupName: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
    virtualNetworkName: !empty(virtualNetworkName) ? virtualNetworkName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    subnetName: subnetNames.endpointsSubnetName
    tags: tags
    principalId: principalId
  }
  dependsOn: [
    virtualNetworkModule
  ]
}

// Get key vault resource
// resource kv 'Microsoft.KeyVault/vaults@2022-07-01' existing = {
//   name: keyVault.outputs.name
//   scope: resourceGroup
// }

// Container Registry
module containerRegistry 'core/containerregistry/containerregistry.bicep' = {
  name: 'containerRegistry'
  scope: containerRegistryResourceGroup
  params: {
    name: !empty(containerRegistryServiceName) ? containerRegistryServiceName : '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: containerRegistryResourceGroupLocation
    tags: tags
    sku: containerRegistrySkuName
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
  dependsOn: [
    keyVault
  ]
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: appServicePlanResourceLocation
    tags: tags
    sku: {
      name: 'B1'
      capacity: 1
    }
    kind: 'linux'
  }
}

// Application frontend service
module frontend 'core/host/appservice.bicep' = {
  name: 'frontend'
  scope: resourceGroup
  params: {
    name: !empty(frontendWebAppName) ? frontendWebAppName : '${abbrs.webSitesAppService}frontend-${resourceToken}'
    location: appServicePlanResourceLocation
    tags: union(tags, { 'azd-service-name': 'frontend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'node'
    runtimeVersion: '18-LTS'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    appSettings: {
      ENVIRONMENT: 'PROD'
    }
    keyVaultName: keyVault.outputs.name
    applicationInsightsName: appInsights.outputs.applicationInsightsName
  }
}

// Keyvault access policies for the services
module servicesKeyVaultAccessPolicies 'core/keyvault/keyvault-access-policy.bicep' = {
  name: 'servicesKeyVaultAccessPolicies'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    accessPolicies: [
      {
        objectId: frontend.outputs.identityPrincipalId
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
    frontend
  ]
}


module openAi 'core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAIResourceName) ? openAIResourceName : '${abbrs.cognitiveServicesOpenAI}${resourceToken}'
    location: openAIResourceGroupLocation
    tags: tags
    sku: {
      name: openAiSkuName
    }
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
    kind: 'AIServices'
    // deployments: deployOpenAIModels && !searchSkipVectorization ? [
    //     {
    //       name: !empty(gpt35TurboDeploymentName) ? gpt35TurboDeploymentName : 'gpt-35-turbo-1106'
    //       sku: {
    //         name: 'Standard'
    //         capacity: 100
    //       }
    //       properties:{
    //         model: {
    //           format: 'OpenAI'
    //           name: 'gpt-35-turbo'
    //           version: !empty(gpt35ModelVersion) ? gpt35ModelVersion : '1106'
    //         }
    //         raiPolicyName: 'Microsoft.Default'
    //       }
    //     }
    //     // {
    //     //   name: !empty(classifierGptDeploymentName) ? classifierGptDeploymentName : 'gpt-35-turbo'
    //     //   model: {
    //     //     format: 'OpenAI'
    //     //     name: !empty(classifierGptModelName) ? classifierGptModelName : 'gpt-35-turbo'
    //     //     version: !empty(classifierGptModelVersion) ? classifierGptModelVersion : '1106'
    //     //   }
    //     //   scaleSettings: {
    //     //     scaleType: 'Standard'
    //     //   }
    //     // }
    //     {
    //       name: !empty(embeddingsGptDeploymentName) ? embeddingsGptDeploymentName : 'text-embedding-ada-002'
    //       sku: {
    //         name: 'Standard'
    //         capacity: 120
    //       }
    //       properties:{
    //         model: {
    //           format: 'OpenAI'
    //           name: !empty(embeddingsGptModelName) ? embeddingsGptModelName : 'text-embedding-ada-002'
    //           version: !empty(embeddingsGptModelVersion) ? embeddingsGptModelVersion : '2'
    //         }
    //         raiPolicyName: 'Microsoft.Default'
    //       }
    //     }
    //   ]: deployOpenAIModels ? [
    //     // {
    //     //   name: !empty(gptDeploymentName) ? gptDeploymentName : 'gpt-4'
    //     //   model: {
    //     //     format: 'OpenAI'
    //     //     name: !empty(gpt4ModelName) ? gpt4ModelName : 'gpt-4'
    //     //     version: !empty(gptModelVersion) ? gptModelVersion : '0314'
    //     //   }
    //     //   scaleSettings: {
    //     //     scaleType: 'Standard'
    //     //   }
    //     // }
    //     // {
    //     //   name: !empty(classifierGptDeploymentName) ? classifierGptDeploymentName : 'gpt-35-turbo'
    //     //   model: {
    //     //     format: 'OpenAI'
    //     //     name: !empty(classifierGptModelName) ? classifierGptModelName : 'gpt-35-turbo'
    //     //     version: !empty(classifierGptModelVersion) ? classifierGptModelVersion : '1106'
    //     //   }
    //     //   scaleSettings: {
    //     //     scaleType: 'Standard'
    //     //   }
    //     // }
    //   ] : []
  }
}


// ToDo: Fix issue through portal - accept RAI. Unable to achieve this through bicep, issue - https://github.com/hashicorp/terraform-provider-azurerm/issues/23580
module multiAccountCogService 'core/ai/cognitiveservices.bicep' = {
  name: 'multiaccountcogservice'
  scope: multiAccountCogServiceResourceGroup
  params: {
    name: !empty(multiAccountCogServiceName) ? multiAccountCogServiceName : '${abbrs.multiAccountCognitiveServices}${resourceToken}'
    kind: 'CognitiveServices'
    location: multiAccountCogServiceResourceGroupLocation
    tags: tags
    sku: {
      name: multiAccountCogServiceSkuName
    }
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
}

module contentSafetyService 'core/ai/cognitiveservices.bicep' = {
  name: 'contentSafety-service'
  scope: contentSafetyResourceGroup
  params: {
    name: !empty(contentSafetyName) ? contentSafetyName : '${abbrs.contentSafety}${resourceToken}'
    kind: 'ContentSafety'
    location: contentSafetyResourceGroupLocation
    tags: tags
    sku: {
      name: contentSafetySkuName
    }
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
}

module documentIntelligenceService 'core/ai/cognitiveservices.bicep' = {
  name: 'documentIntelligence-service'
  scope: documentIntelligenceResourceGroup
  params: {
    name: !empty(documentIntelligenceName) ? documentIntelligenceName : '${abbrs.cognitiveServicesFormRecognizer}${resourceToken}'
    kind: 'FormRecognizer'
    location: documentIntelligenceResourceGroupLocation
    tags: tags
    sku: {
      name: documentIntelligenceSkuName
    }
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
  }
}

module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  scope: searchServiceResourceGroup
  params: {
    name: !empty(searchServiceName) ? searchServiceName : '${abbrs.azureAISearchServices}${resourceToken}'
    searchIndexName: searchIndexName
    location: searchServiceResourceGroupLocation
    tags: tags
    // authOptions: {
    //   aadOrApiKey: {
    //     aadAuthFailureMode: 'http401WithBearerChallenge'
    //   }
    // }
    sku: {
      name: searchServiceSkuName
    }
    // semanticSearch: 'free'
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
    kbFieldsContent: 'content'
    kbFieldsCategory: 'category'
    kbFieldsSourcePage: 'sourcepage'
    skipVectorization: searchSkipVectorization
    createPrivateEndpoint: createPrivateEndpoint
    virtualNetworkResourceGroupName: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
    virtualNetworkName: !empty(virtualNetworkName) ? virtualNetworkName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    subnetName: subnetNames.endpointsSubnetName
  }
  dependsOn: [
    keyVault
    virtualNetworkModule
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
      name: 'Standard_LRS'
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
      {
        name: storageImageContainerName
        publicAccess: 'None'
      }
    ]
    storageContainerName: storageContainerName
    storageImageContainerName: storageImageContainerName
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
    createPrivateEndpoint: true
    virtualNetworkName: !empty(virtualNetworkName) ? virtualNetworkName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    subnetName: subnetNames.endpointsSubnetName 
  }
  dependsOn: [
    keyVault
    virtualNetworkModule
  ]
}

// Virtual Network Deployment
module virtualNetworkModule 'core/network/vnet.bicep' = {
  name: 'virtualNetwork'
  scope: resourceGroup
  params: {
    vnetName: !empty(virtualNetworkName) ? virtualNetworkName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    addressSpace: virtualNetworkAddressPrefix
    aksSubnetName: subnetNames.aksSubnetName
    aksSubnetPrefix: subnetPrefixes.aksSubnetPrefix
    appGatewaySubnetName: subnetNames.appGatewaySubnetName
    appGatewaySubnetPrefix: subnetPrefixes.appGatewaySubnetPrefix
    endpointsSubnetName: subnetNames.endpointsSubnetName
    endpointsSubnetPrefix: subnetPrefixes.endpointsSubnetPrefix
    location: location
    tags: tags
  }
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
    location: location
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
    createPrivateEndpoint: createPrivateEndpoint
    privateEndpointName: !empty(cosmosPrivateEndpointName) ? cosmosPrivateEndpointName : '${abbrs.cosmosNoSQLDBDatabaseAccounts}${resourceToken}-pe'
    virtualNetworkResourceGroupName: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
    virtualNetworkName: !empty(virtualNetworkName) ? virtualNetworkName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    subnetName: subnetNames.endpointsSubnetName
    tags: tags
  }
  dependsOn: [
    keyVault
    virtualNetworkModule
  ]
}

// App Insights Deployment 
module appInsights 'core/logging/appinsights.bicep' = {
  name: 'app-insights'
  scope: appInsightsResourceGroup
  params: {
    applicationInsightsName : !empty(appInsightsName) ? appInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    logAnalyticsWorkspaceName: !empty(logAnalyticsWorkspaceName) ? logAnalyticsWorkspaceName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: appInsightsResourceLocation
    addKeysToVault: true
    keyVaultName: keyVault.outputs.name
    tags: tags
  }
  dependsOn: [
    keyVault
  ]
}

// AKS Deployment
module aksManagedCluster 'core/aks/aks.bicep' = {
  name: aksClusterName
  scope: aksResourceGroup
  params: {
    aksName: aksClusterName
    location: aksClusterLocation
    agentPoolVMSize: aksAgentPoolVMSize
    userPoolVMSize: aksUserPoolVMSize
    dnsPrefix: aksClusterName
    kubernetesVersion: aksVersion
    appGatewayName: !empty(appGatewayName) ? appGatewayName : 'appgw-${abbrs.networkApplicationGateways}${resourceToken}'
    tags: tags
    keyVaultName: keyVault.outputs.name
    virtualNetworkName: !empty(virtualNetworkName) ? virtualNetworkName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    aksSubnetName: subnetNames.aksSubnetName
    appGatewaySubnetCIDR: subnetPrefixes.appGatewaySubnetPrefix
  }
  dependsOn: [
    keyVault
    virtualNetworkModule
  ]
}

module aksManagedIdentityPrincipalId 'core/keyvault/keyvault-secret.bicep' = {
  name: 'aks-managed-identity-principal-id'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    secretName: 'AKS-MANAGED-IDENTITY-PRINCIPAL-ID'
    secretValue: aksManagedCluster.outputs.aksManagedIdentityPrincipalId
  }
  dependsOn: [
    keyVault
    aksManagedCluster
    virtualNetworkModule
  ]
}


// module azureOpenAIEmbeddingsEngineName 'core/keyvault/keyvault-secret.bicep' = {
//   name: 'openai-secret-embeddings-engine-name'
//   scope: resourceGroup
//   params: {
//     keyVaultName: keyVault.outputs.name
//     secretName: 'AZURE-OPENAI-EMBEDDINGS-ENGINE-NAME'
//     secretValue: embeddingsGptModelName
//   }
//   dependsOn: [
//     keyVault
//     openAi
//   ]
// }

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


output KEYVAULT_NAME string = keyVault.outputs.name
output AZURE_RESOURCE_GROUP string = resourceGroup.name
// output AKS_CLUSTER_NAME string = aksManagedCluster.name
