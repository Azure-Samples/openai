param name string
param location string = resourceGroup().location
param tags object = {}
param sku object = {
  family: 'A'
  name: 'standard'
}
param enabledForDeployment bool = true
param enabledForDiskEncryption bool = false
param enabledForTemplateDeployment bool = true
param principalId string

param createPrivateEndpoint bool = false
param privateEndpointName string = '${name}-pe'
param virtualNetworkResourceGroupName string = resourceGroup().name
param virtualNetworkName string
param subnetName string
param privateDnsZoneName string = 'privatelink.vaultcore.azure.net'

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: sku.family
      name: sku.name
    }
    tenantId: subscription().tenantId
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: principalId
        permissions: {
          secrets: ['get', 'list', 'set', 'delete']
        }
      }
    ]
    enabledForDeployment: enabledForDeployment
    enabledForDiskEncryption: enabledForDiskEncryption
    enabledForTemplateDeployment: enabledForTemplateDeployment
  }
}

// Private Endpoint for Blob Storage
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2021-08-01' = if (createPrivateEndpoint) {
  name: privateEndpointName
  location: location
  properties: {
    subnet: {
      id: resourceId(virtualNetworkResourceGroupName, 'Microsoft.Network/virtualNetworks/subnets', virtualNetworkName, subnetName)
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointName}-keyVaultConnection'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: [
            'vault' // Change this if using a different API
          ]
          requestMessage: 'Please approve the connection.'
        }
      }
    ]
  }
}

// Private DNS Zone for the endpoint
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneName
  location: 'global'
  tags: tags
}

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
}

// Private DNS Zone Group to link DNS zone with the private endpoint
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-02-01' = {
  name: '${privateEndpointName}-dnsZoneGroup'
  parent: privateEndpoint
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'default'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}


output id string = keyVault.id
output name string = keyVault.name
