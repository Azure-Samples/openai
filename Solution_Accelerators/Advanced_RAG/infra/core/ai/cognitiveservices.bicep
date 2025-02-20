param name string
param location string = resourceGroup().location
param tags object = {}

@description('Cognitive Service Type')
@allowed([ 'CognitiveServices', 'AIServices', 'ContentSafety', 'FormRecognizer' ])
param kind string = 'CognitiveServices'

param customSubDomainName string = name
param deployments array = []
param publicNetworkAccess string = 'Enabled'
param networkAcls object = {
  defaultAction: 'Allow'
  ipRules: []
  virtualNetworkRules: []
}
param sku object = {
  name: 'S0'
}

@description('Key Vault name')
param keyVaultName string = ''

@description('Add secrets to Key Vault')
param addKeysToVault bool = true

@description('Disable local authentication')
param disableLocalAuth bool = true

resource account 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: kind
  properties: {
    networkAcls: networkAcls
    customSubDomainName: customSubDomainName
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: disableLocalAuth
  }
  sku: sku
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [for deployment in deployments: {
  parent: account
  name: deployment.name
  properties: {
    model: deployment.model
    raiPolicyName: deployment.?raiPolicyName ?? null
    scaleSettings: deployment.scaleSettings
  }
}]

// Modules for 'CogService' type
module azureCogServiceKey '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'CognitiveServices' && !disableLocalAuth) {
  name: 'cogServiceKey'
  params: {
    keyVaultName: keyVaultName
    secretName: 'SPEECH-KEY'
    secretValue: listKeys(account.id, '2022-10-01').key1
  }
}

// Modules for 'ContentSafety' type
module azureContentSafetyKeySecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'ContentSafety' && !disableLocalAuth) {
  name: 'contentSafetyKey'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-CONTENT-SAFETY-API-KEY'
    secretValue: listKeys(account.id, '2022-10-01').key1
  }
}

module azureContentSafetyServiceSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'ContentSafety') {
  name: 'contentSafetyService'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-CONTENT-SAFETY-SERVICE'
    secretValue: account.name
  }
}

// Modules for 'AzureOpenAI' type
module azureOpenAIServiceEndpointSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'AzureOpenAI') {
  name: 'azureOpenAIServiceEndpoint'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-OPENAI-SERVICE-ENDPOINT'
    secretValue: account.properties.endpoint
  }
}

module azureOpenAIServiceKeySecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'AzureOpenAI' && !disableLocalAuth) {
  name: 'azureOpenAIServiceKey'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-OPENAI-SERVICE-KEY'
    secretValue: listKeys(account.id, '2022-10-01').key1
  }
}

module formRecognizerEndpointSecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'FormRecognizer') {
  name: 'formRecognizerEndpoint'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-DOCUMENT-INTELLIGENCE-ENDPOINT'
    secretValue: account.properties.endpoint
  }
}

module formRecognizeKeySecret '../keyvault/keyvault-secret.bicep' = if(addKeysToVault && kind == 'FormRecognizer' && !disableLocalAuth) {
  name: 'formRecognizerKey'
  params: {
    keyVaultName: keyVaultName
    secretName: 'AZURE-DOCUMENT-INTELLIGENCE-KEY'
    secretValue: listKeys(account.id, '2022-10-01').key1
  }
}


output endpoint string = account.properties.endpoint
output id string = account.id
output name string = account.name
