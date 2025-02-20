var sku = {
  name: 'Base'
  tier: 'Standard'
}

param location string = ''
param aksName string = ''
param dnsPrefix string = ''
param agentPoolVMSize string = ''
param userPoolVMSize string = ''
param tags object = {
  Purpose: ''
}
param kubernetesVersion string = ''
param appGatewayName string = ''
param appGatewaySubnetCIDR string = ''

param keyVaultName string = ''

// Parameters for VNet and Subnet
param virtualNetworkName string = ''
param vnetResourceGroupName string = resourceGroup().name
param aksSubnetName string = ''

// Supported OS Images for VMSS
@allowed([
  '18.04-LTS'
  '18_04-LTS-Gen2'
  '20_04-LTS'
  '20_04-LTS-Gen2'
  '22_04-LTS'
  '22_04-LTS-Gen2'
])
param osSku string = '22_04-LTS'


// Get the VNet Subnet Resource ID
resource vnet 'Microsoft.Network/virtualNetworks@2022-05-01' existing = {
  name: virtualNetworkName
  scope: resourceGroup(vnetResourceGroupName)
}

resource vnetSubnet 'Microsoft.Network/virtualNetworks/subnets@2022-05-01' existing = {
  name: aksSubnetName
  parent: vnet
}


resource managedAKSCluster 'Microsoft.ContainerService/managedClusters@2024-03-02-preview' = {
  name: aksName
  location: location
  sku: sku
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    autoUpgradeProfile: {
      nodeOSUpgradeChannel: 'NodeImage'
      upgradeChannel: 'stable'
    }
    agentPoolProfiles: [
      {
        name: 'agentpool'
        count: 1
        vmSize: agentPoolVMSize
        osType: 'Linux'
        osSKU: osSku
        type: 'VirtualMachineScaleSets'
        mode: 'System'
        enableAutoScaling: false
        vnetSubnetID: vnetSubnet.id
        tags: tags
      }
      {
        name: 'userpool'
        count: 1
        vmSize: userPoolVMSize
        osType: 'Linux'
        osSKU: osSku
        type: 'VirtualMachineScaleSets'
        mode: 'User'
        enableAutoScaling: false
        vnetSubnetID: vnetSubnet.id
        tags: tags
      }
    ]
    dnsPrefix: dnsPrefix
    addonProfiles: {
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: {
          enableSecretRotation: 'false'
          rotationPollInterval: '2m'
        }
      }
      azurepolicy: {
        enabled: false
      }
      ingressApplicationGateway: {
        enabled: true
        config: {
          applicationGatewayName: appGatewayName
          subnetCIDR: appGatewaySubnetCIDR
        }
      }
    }
    networkProfile: {
      networkPlugin: 'azure'
    }
  }
  tags: tags
}

module kvAccessPolicy '../keyvault/keyvault-access-policy.bicep' = {
  name: 'kvAccessPolicy'
  params: {
    keyVaultName: keyVaultName
    accessPolicies: [
      {
        tenantId: managedAKSCluster.identity.tenantId
        objectId: managedAKSCluster.identity.principalId
        permissions: {
          secrets: [ 'get', 'list' ]
        }
      }
    ]
  }
}

output aksManagedIdentityPrincipalId string = managedAKSCluster.identity.principalId
