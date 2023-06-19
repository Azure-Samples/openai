param sqlServerName string
param sqlAdminLogin string = 'azureuser'

@secure()
param sqlAdminPassword string = newGuid()

param sqlDatabaseName string
param databaseCollation string = 'SQL_Latin1_General_CP1_CI_AS'
param databaseMaxSizeBytes int = 34359738368 // 32 GB
param location string
param tags object = {}

@description('Key Vault ID')
param keyVaultName string = ''

@description('Key Vault ID')
param addKeysToVault bool = false

resource sqlServer 'Microsoft.Sql/servers@2022-08-01-preview' = {
  name: sqlServerName
  location: location
  tags: tags
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2022-08-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  properties: {
    collation: databaseCollation
    maxSizeBytes: databaseMaxSizeBytes
  }
}

module sqlConnectionStringSecret '../keyvault/keyvault_secret.bicep' = if(addKeysToVault) {
  name: 'SQL-CONNECTION-STRING'
  params: {
    keyVaultName: keyVaultName
    secretName: 'SQL-CONNECTION-STRING'
    secretValue: concat('Driver={ODBC Driver 18 for SQL Server};',
     'Server=tcp:',
     sqlServer.properties.fullyQualifiedDomainName, 
     ',1433;Database=', sqlDatabaseName, 
     ';UiD=', sqlAdminLogin, 
     ';Pwd=', sqlAdminPassword, 
     ';Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;')
  }
}

output sqlServerName string = sqlServer.name
output sqlServerFqdn string = '${sqlServerName}.database.windows.net'
output databaseName string = sqlDatabase.name
