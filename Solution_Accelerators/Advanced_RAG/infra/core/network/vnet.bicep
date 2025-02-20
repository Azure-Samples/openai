// Define parameters
param location string = resourceGroup().location
param vnetName string
param appGatewaySubnetName string
param aksSubnetName string
param endpointsSubnetName string
param addressSpace string
param appGatewaySubnetPrefix string
param aksSubnetPrefix string
param endpointsSubnetPrefix string

@description('Tags to apply to resources')
param tags object = {}

// Create the Virtual Network
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-02-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        addressSpace
      ]
    }
    // subnets: [
    //   {
    //     name: appGatewaySubnetName
    //     properties: {
    //       addressPrefix: appGatewaySubnetPrefix
    //     }
    //   }
    // ]
  }
}

// Network Security Group for Endpoints Subnet
// ToDo: Restrict the traffic to only the required
resource endpointsNSG 'Microsoft.Network/networkSecurityGroups@2023-02-01' = {
  name: 'endpointsNSG'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowPrivateEndpoints'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

// Subnets and NSG Associations
resource aksSubnetandNSGAssociation 'Microsoft.Network/virtualNetworks/subnets@2023-02-01' = {
  parent: virtualNetwork
  name: aksSubnetName
  properties: {
    addressPrefix: aksSubnetPrefix
  }
}

resource endpointsSubnetNSGAssociation 'Microsoft.Network/virtualNetworks/subnets@2023-02-01' = {
  parent: virtualNetwork
  name: endpointsSubnetName
  properties: {
    addressPrefix: endpointsSubnetPrefix
    networkSecurityGroup: {
      id: endpointsNSG.id
    }
  }
}
