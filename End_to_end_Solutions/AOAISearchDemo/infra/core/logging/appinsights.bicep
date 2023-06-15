@description('Azure region of the deployment')
param location string = resourceGroup().location

@description('Tags to add to the resources')
param tags object = {}

@description('Application Insights resource name')
param applicationInsightsName string

@description('Log Analytics resource name')
param logAnalyticsWorkspaceName string 

@description('Key Vault ID')
param keyVaultName string = ''

@description('Key Vault ID')
param addKeysToVault bool = false

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Disabled'
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName 
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    Flow_Type: 'Bluefield'
  }
}

module appInsightsConnectionStringSecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'APPLICATION-INSIGHTS-CNX-STRING'
  params: {
    keyVaultName: keyVaultName
    secretName: 'APPLICATION-INSIGHTS-CNX-STRING'
    secretValue: applicationInsights.properties.ConnectionString
  }
}

output applicationInsightsId string = applicationInsights.id
