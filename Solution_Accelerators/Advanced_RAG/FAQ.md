# FAQ

### Why did my deployment fail?
<!-- From infra README-->
In most cases the deployment will fail due to unavailability of certain resources in certain regions. The `azd provision` command will output the following:
1. Deployment URL, which you can click on and browse to see the details of the deployment and any error details
2. Progress of various resource deployments
3. Failures, if any

If the failure is due to resource location or SKU/type restrictions, update the `main.parameters.json` or directly the `main.bicep` file accordingly and rerun `azd provision`.

Deployment failures can occur if there are quota limitations or if the selected region does not support the required resources. Additionally, network interfaces and other resources may need to be deleted before re-provisioning the deployment. Here are some best practices and steps to follow to resolve these issues:

- Check Quota and Region Support: Ensure that the region you are deploying to supports the required resources and that you have sufficient quota. You can check and request quota increases through the Azure portal.

- Delete Network Interfaces and Other Resources: If the deployment fails due to Azure OpenAI (AOAI) resource issues, you may need to delete certain resources in a specific order. Here is the recommended order of deletion:
    - Detach Network Security Group (NSG)
    - Delete Network Interface Card (NIC)
    - Delete Subnet
    - Delete Virtual Network (VNet)
    - Delete Web App
    - Delete Service Plan
    - Delete Private DNS

- Delete Resource Group (RG): If the above steps do not resolve the issue, consider deleting the entire resource group and re-running the deployment. This ensures that all associated resources are cleaned up properly.

Use Code Snippets for Automation: To streamline the process, you can use code snippets to automate the deletion of resources. Here are some examples:

Using Azure CLI:

```
az network nsg delete --name <your-nsg-name> --resource-group <your-resource-group>
az network nic delete --name <your-nic-name> --resource-group <your-resource-group>
az network vnet subnet delete --name <your-subnet-name> --vnet-name <your-vnet-name> --resource-group <your-resource-group>
az network vnet delete --name <your-vnet-name> --resource-group <your-resource-group>
az webapp delete --name <your-webapp-name> --resource-group <your-resource-group>
az appservice plan delete --name <your-service-plan-name> --resource-group <your-resource-group>
az network private-dns zone delete --name <your-private-dns-name> --resource-group <your-resource-group>
```

Using Azure PowerShell:

```
Remove-AzNetworkSecurityGroup -Name <your-nsg-name> -ResourceGroupName <your-resource-group> -Force
Remove-AzNetworkInterface -Name <your-nic-name> -ResourceGroupName <your-resource-group> -Force
Remove-AzVirtualNetworkSubnetConfig -Name <your-subnet-name> -VirtualNetworkName <your-vnet-name> -ResourceGroupName <your-resource-group> -Force
Remove-AzVirtualNetwork -Name <your-vnet-name> -ResourceGroupName <your-resource-group> -Force
Remove-AzWebApp -Name <your-webapp-name> -ResourceGroupName <your-resource-group> -Force
Remove-AzAppServicePlan -Name <your-service-plan-name> -ResourceGroupName <your-resource-group> -Force
Remove-AzPrivateDnsZone -Name <your-private-dns-name> -ResourceGroupName <your-resource-group> -Force
```

By following these steps and best practices, you can ensure a smoother deployment process and avoid common roadblocks related to quota and region support limitations.


### Why does my deployment fail with a key vault naming issue?

A common reason for deployment failures related to key vaults is the soft delete feature. When you delete a resource group (RG) that contains a key vault, the key vault is not permanently deleted but rather soft deleted. This means that the name of the key vault remains reserved and cannot be reused until it is purged.

If you encounter an error stating that the key vault name is already in use, it could be because of this soft delete feature. To resolve this issue, you need to purge the soft-deleted key vault before attempting to provision it again.

Here are steps to purge a soft-deleted key vault:

Using Azure CLI:

```
az keyvault purge --name <your-key-vault-name>
```

Using Azure PowerShell:

```
Remove-AzKeyVault -VaultName <your-key-vault-name> -InRemovedState -Force
```

### How can I use my own Azure Resources?

You can use your own Azure Resources by updating the [main.bicep](infra/main.bicep) file. For example, if you want to use your own Azure Open AI Resource, update the following parameters:

```
param openAIResourceGroupName string = <your-resource-group>
param openAIResourceGroupLocation string = '<your-resource-location>'
param openAIResourceName string = <your-resource-name>
```

### Why am I seeing Error Code 404 - DeploymentNotFound?

This error occurs when the Azure OpenAI deployment does not exist or is not accessible. Ensure that the deploymentName in prompt_config.yaml exactly matches the Azure OpenAI deployment name created in Azure. If you recently created the deployment, wait a few minutes and try again. Also, verify in the Azure portal that the deployment exists under your Azure OpenAI resource.


### Why am I seeing ClientAuthenticationError (PermissionDenied)?
This error occurs when your user or service principal does not have the necessary permissions to access the resource or API operation. Ensure that you have the correct permissions assigned in Azure for the specific resource. You can check and update permissions in the Azure Portal → Access Control (IAM) section of the resource.


### Why am I seeing a permission error when searching the index?
This error occurs because your account or service principal does not have the "Search Index Data Reader" role assigned for the selected index. Ask your service administrator to grant you this role in the Azure Portal → Access Control (IAM) section of your Azure AI Search resource.

### How to keep my data updated?
It is best that you have a schedule for re-running ingestion with every new set of data to make sure your index is updated. To do so follow instructions [here.](./src/skills/ingestion/README_FINANCIAL.md/#running-ingestion-service-locally)

### Why is my frontend deployment script taking long?
Frontend Deployment needs to compress Node build files, this can take a while using using built in Windows Zip. To speed up the process install 7Zip (https://www.7-zip.org/).
Navigate to src/frontend_rag (or src/frontend_retail), run:
> npm install

> npm run build

Zip up the contents of src/frontend_rag (or src/frontend_retails) (including the build and source files) using 7zip and run these two commands:
> az webapp config set --resource-group $resourceGroup --name $webAppName --startup-file "npm start"

> az webapp deployment source config-zip --resource-group $resourceGroup --name $webAppName --src $zipFilePath

($zipFilePath is path where you created the zip file, find the $resourceGroup and $webAppName in Azure from your deployment process)

## What access do I need to run the solution locally?

To run the solution locally, ensure you have the following role assignments:

- **Azure Storage**: `Storage Blob Data Contributor`
- **Azure OpenAI**: `Cognitive Services OpenAI User` or `Cognitive Services OpenAI Contributor`
- **Azure Search Service**: `Search Index Data Contributor`, `Search Index Data Reader`
- **Azure Cosmos DB**: `Cosmos DB Built-in Data Contributor`