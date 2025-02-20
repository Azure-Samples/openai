// roleAssignment.bicep

// param principalId string
// param roleDefinitionId string = subscriptionResourceId(
//   'Microsoft.Authorization/roleDefinitions',
//   'b24988ac-6180-42a0-ab88-20f7382dd24c' // Network Contributor role
// )
// param resourceScope resource

// var roleAssignmentGuid = guid(resourceScope.id, principalId, roleDefinitionId)

// resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
//   name: roleAssignmentGuid
//   scope: resourceScope
//   properties: {
//     roleDefinitionId: roleDefinitionId
//     principalId: principalId
//     principalType: 'ServicePrincipal'
//   }
// }
