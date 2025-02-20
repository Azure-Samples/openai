param appServiceName string = ''
param allowedIpAddresses array = []

var accessRules = [for ip in allowedIpAddresses: {
  name: 'Allow ${ip}'
  description: 'Allow access from ${ip}'
  action: 'Allow'
  priority: 1
  ipAddress: '${ip}/8'
}]

resource webConfig 'Microsoft.Web/sites/config@2022-03-01' = {
  name: 'web'
  parent: appService
  properties: {
    ipSecurityRestrictions: union(accessRules, [
      {
        name: 'Deny all'
        description: 'Deny all access'
        action: 'Deny'
        priority: 2147483647
        ipAddress: 'Any'
      }
    ])
  }
}

resource appService 'Microsoft.Web/sites@2022-03-01' existing = if (!(empty(appServiceName))) {
  name: appServiceName
}
