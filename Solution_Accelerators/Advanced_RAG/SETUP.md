# Getting Started

## Table of Contents
- [Azure Setup](#azure-setup)
  - [Prerequisite](#prerequisite)
  - [Deployment Steps](#deployment-steps)
  - [Manual Configuration](#manual-configuration)
    - [AKS](#aks)
    - [Application Gateway](#application-gateway)
    - [CosmosDB](#cosmosdb)
    - [Keyvault](#keyvault)
    - [Azure OpenAI](#azure-openai)
    - [Azure AI Search](#azure-ai-search)
    - [Creating App registration for user Authentication with EntraID](#creating-app-registration-for-user-authentication-with-entraid)
- [Local Setup](#local-setup)
  - [Deployment Prerequisites](#deployment-prerequisites)
  - [Deploy Azure Resources](#deploy-azure-resources)
  - [CosmosDB Emulator](#cosmosdb-emulator)
  - [Redis](#redis)
  - [Project Initialization](#project-initialization)
    - [Frontend](#frontend)
    - [Core Microservices](#core-microservices)
  - [Ingesting Financial data for testing](#ingesting-financial-data-for-testing)
  - [Testing and Evaluation](#testing-and-evaluation)
  - [Instrumentation and application logs](#instrumentation-and-application-logs)
- [Build Your Own Copilot](#build-your-own-copilot)
- [Guidance](#guidance)
- [Additional Resources](#additional-resources)

## Azure Setup
![Infrastructure Overview Diagram](./docs/media/infrastructure_overview.png)

### Prerequisite
The deployment automation is based on [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/reference). Follow steps [here](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux&pivots=os-windows) to install/update Azure Developer CLI
> Run Install-Module Az.Accounts\
> Run Install-Module Az.Resources

### Deployment Steps
1. Login to [portal.azure.com](portal.azure.com). If you do not have an Azure account, you should create one. Visit [here](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account/)

2. Create a new Resource Group (similar to a folder in windows explorer) where all the Azure resources for this PoC would be created. Select the region where these resources needs to be created.

3. Note the Resource Group name, Region and your Azure subscription ID. These will be needed for the later steps

4. Open Windows powershell window and change directory to root of this repo: `<repo root>\multimodalbot`

5. type `azd init` and hit enter. This will ask for an environment name. Provide a name - say `rag_demo`. You should see a success message that the environment was initialized.\
If you open windows explorer and go to the root of this repo `<repo root>\multimodalbot`, there should be folder with name `.azure`. The `.azure` will have `rag_demo` folder with a .env file.

6. Open the .env file and, then add the following lines to the .env file and save it.

    ```
    AZURE_LOCATION="Azure Resource Group location"
    AZURE_RESOURCE_GROUP="Azure Resource Group to use"
    AZURE_SUBSCRIPTION_ID="Your Azure Subscription ID"
    ```
    The .env file should look something like this
    ```
    AZURE_ENV_NAME="rag_demo"
    AZURE_RESOURCE_GROUP="demotest"
    AZURE_LOCATION="west us"
    AZURE_SUBSCRIPTION_ID="SubscriptionID_GUID"
    ```

7. Open the `<repo root>\multimodalbot\infra\main.parameters.json` file. This file has parameters that can be passed to the various Azure resources when creating them. Right now the scripts would create a web app for the frontend, name of which is as below. Change them to meet your naming conventions:

    ```
    "frontendWebAppName": {
      "value": "financial-rag-demo-fe"
    }
    ```

    If the deployment succeeds, a web app - https://financial-rag-demo-fe.azurewebsites.net will be created. This is where the front end web app code could be deployed to.

    >Note: These web app names should be unique across azurewebsites.net domain.

8. Review/update the AKS region and VMs used for AKS to ensure those VMs are available in your region:

    ```
    "aksClusterLocation": {
          "value": "westus2"
        },
        "aksVersion": {
          "value": "1.29.7"
        },
        "aksAgentPoolVMSize": {
          "value": "standard_a2m_v2"
        },
        "aksUserPoolVMSize": {
          "value": "standard_a2m_v2"
        },
    ```

9. Review/update the CIDRs for virtual networks and subnets.

    ```
        "virtualNetworkAddressPrefix": {
          "value": "10.255.0.0/16"
        },
        "subnetPrefixes": {
          "value": {
            "aksSubnetPrefix": "10.255.1.0/24",
            "endpointsSubnetPrefix": "10.255.101.0/24",
            "appGatewaySubnetPrefix": "10.255.201.0/24"
          }
        }
    ```

10. You can also set tag (a dictionary of key value pairs) with each resource created. To set that, update the value of the tag parameter:
    ```
    "tag": {
          "value": {
            "Purpose": "Resources for copilot demo"
          }
        }
    ```
    >Note: If you have access to multiple Azure subscriptions you could set the context to the right subscription by running `az account set --subscription <subscription ID>` command first on the powershell prompt.

11. The script will deploy following resources. For the deployment to be successful, it's best to find a region where there is enough quota to deploy these resources. If you have existing resources that you want to use, then update the [main.parameters.json](./infra/main.parameters.json) file and/or the [main.bicep](./infra/main.bicep) file to include the resource group, resource name, and location of the existing resource. Otherwise, the script will try to create them in the resource group and location specified above.

    1. Azure OpenAI
    2. Azure AI Services
    3. Azure AI Search
    4. Storage Account
    5. Azure Cosmos DB
    6. Application Insights
    7. Container Registry
    8. Azure AI Content Safety
    9. Document Intelligence
    10. AKS
    11. Azure Key Vault
    12. Web App and Web App plan
    13. Virtual network and subnets


Once all the parameters looks good, go back to powershell window and type `azd provision` and hit enter.
```
(venv) PS C:\Repo\MultiModalBot> azd provision
```
`azd provision` will try to install all the resources in the selected resource group. It will open your browser to authenticate you to the Azure portal and then continue with the deployment. If all goes well, you should see a message on the command prompt that the application was provisioned, otherwise try to fix the resource deployment issues before proceeding to the next steps of doing some manual updates and configurations.


> **Note:** The most common reason the script fails is due to the unavailability of a resource in the specified region. If failures occur, especially during the creation of vNets and subnets, it is best to delete the resources and start again. However, some resources like Key Vault and CosmosDB have specific deletion processes:
> - **Key Vault:** Key Vault has delete protection, so you may need to purge it completely if you want to delete it. Use the following command in Azure Cloud Shell:
>   ```
>   az keyvault purge --name <YourKeyVaultName> --location <YourKeyVaultLocation>
>   ```
> - **CosmosDB:** CosmosDB can take time to be deleted and recreated with the same name. Ensure it is fully deleted before attempting to recreate it. You can check the deletion status in the Azure portal.

### Manual Configuration

#### AKS
**Note:**
Setting up of AKS and application gateway is only needed if you want the services to be deployed to cloud. Users can proceed with setting up the keyvault and then follow the instructions to [run the solution locally in VSCode](#local-setup). Once that succeeds, they can then come and setup the AKS.

1. To work with the AKS cluster, developers will need `Azure Kubernetes Service RBAC Admin` role assigned.

2. Run the get-credential command and authenticate using kubelogin
    ```
    az aks get-credentials --resource-group <RESOURCE GROUP NAME> --name <CLUSTER NAME>
    kubelogin convert-kubeconfig -l azurecli
    ```

3. Update the secrets_provider.yaml file in the `<repo root>\multimodalbot\infra\aks_post_provision` folder  to update `KEYVAULTNAME` name and `TENANTID`, which can be found from your recent deployment of the Azure resources. Save the file.

4. Run kubectl apply command to apply these changes to AKS cluster. Change directory to `<repo root>\multimodalbot\infra` and run:
    ```
    kubectl apply -f .\aks_post_provision\secrets_provide.yaml
    ```

5. Deploy redis pods to AKS.
    1. Review the `<repo root>\multimodalbot\infra\aks_post_provision\redis_deployment.yaml` file for redis password used
    2. Change directory to `<repo root>\multimodalbot\infra` and run:\
      `
      kubectl apply -f .\aks_post_provision\redis_deployment.yaml
      `
    3. Add following secret name and values to the keyvault:

          | Secret Name     | Value            |
          |-----------------|------------------|
          | `REDIS-HOST`    | `localhost`      |
          | `REDIS-PORT`    | `6379`           |
          | `REDIS-PASSWORD`| `redis_password` |

6. Attach AKS to appropriate ACR either through the portal(overview tab of AKS) or by the below commands:

    1. Get ACR Resource ID (NOTE: Use the ACR in the prod resource group)

        ```
        az acr show --resource-group <PROD RESOURCE GROUP> --name <PROD ACR NAME> --query id -o tsv
        ```

    2. Attach AKS to ACR (ACR is from the prod resource group)
        ```
        az aks update --name <CLUSTER NAME> --resource-group <RESOURCE GROUP NAME> --attach-acr /subscriptions/SUBSCRIPTION-ID/resourceGroups/<PROD RESOURCE GROUP>/providers/Microsoft.ContainerRegistry/registries/<PROD ACR NAME>
        ```

7. Grant VMSS system identity to GET and LIST secrets from keyvault using keyvault access policies

    1. Find the resource group created by AKS Provisioning Process, you can find this under "Properties" in the AKS Resource.
    ![Find Resource Group](./docs/media/find_resource_group.png)
    2. Find the virtual machine scale set resource in this resource group
    ![VMSS Resource](./docs/media/resource_group_vmss.png)
    3. In this resource group click on identity in the left panel and set System Identity to "ON"
    ![Identity](./docs/media/identity.png)
    4. Copy the Object Principal ID that is created. Navigate to the Main Resource Group and find keyvault from the list of resources.
    In Keyvault, Go to "Access Policies" > "Create" > Select "Get" and "List" under "Secret Permissions" > Click "Next" > Find the Principal using the Object Principal ID we copied earlier > Click "Create" under "Review + Create"

#### Application Gateway
1. Navigate to the AKS Resource Group and find the Public IP address created by the provisioning process
![Public IP Resource](./docs/media/resource_group_publicip.png)
In the Public IP resource navigate to configuration and set a DNS name label
![Public IP Resource](./docs/media/public_ip_dns.png)

2. Install Cert Manager in the AKS Cluster by following instructions [here](https://cert-manager.io/docs/tutorials/getting-started-aks-letsencrypt/#install-cert-manager)

3. Create a Cert Manager cluster issuer in the AKS Cluster, to do this apply the following YAML to the cluster `/infra/aks_post_provision/cluster_issuer.yaml`. Make sure to add your email address in the cluster_issuer.yaml file.

4. Create a App Gateway ingress in your cluster, to do this apply the following YAML to the cluster `/infra/aks_post_provision/aks_app_gateway_ingress.yaml`. Make sure replace "host" with the full DNS name label set in the previous set.

#### CosmosDB
1. To work with CosmosDB and it's data plane, developers need to enable their public IP address through the networking tab. Once below updates are done, public IP address can be disabled.
Additionally, developers would need `Cosmos DB Built-in Data Contributor` role which can be assigned using either the built-in role directly or registering a custom role.
  - Option A : Built-in role

    Run
    ```
    az cosmosdb sql role assignment create --account-name <cosmos account name> --resource-group <resource group> --principal-id <principal id> --role-definition-id 00000000-0000-0000-0000-000000000002 --scope "/"
    ```

- Option B : Custom role

  Run
  ```
  az cosmosdb sql role definition create --resource-group "<name-of-existing-resource-group>" --account-name "<name-of-existing-nosql-account>" --body ".\custom_roles\cosmosReadWrite.json"
  az cosmosdb sql role assignment create --resource-group "<name-of-existing-resource-group>" --account-name "<name-of-existing-nosql-account>" --role-definition-id "<id-of-new-role-definition>" --principal-id "<id-of-existing-identity>" --scope "/subscriptions/aaaa0a0a-bb1b-cc2c-dd3d-eeeeee4e4e4e/resourceGroups/msdocs-identity-example/providers/Microsoft.DocumentDB/databaseAccounts/msdocs-identity-example-nosql"
  ```

2. In order to access CosmosDB resource from other resources such as services running within AKS, `Cosmos DB Built-in Data Contributor` role needs to be assigned using one of the above mentioned options.

3. Manually add the following `anonymous` user profile in entities container in the CosmosDB database
    ```
    {
        "user_name": "Anonymous",
        "description": "No user information.",
        "gender": "Other",
        "id": "anonymous",
        "partition_key": "user"
    }
    ```

#### Keyvault
1. To work with keyvault, developers will need GET, LIST and SET permissions to keyvault secrets. Refer [AKS](#aks) to grant these permissions via access policies tab.
2. Navigate through `config.py` files across micro-services in the `<repo root>\multimodalbot\src` folder: config_hub, skill\search, orchestrator_rag, data, session_manager and add any un-populated secrets with appropriate values in the keyvault. Examples:
    ```
    az keyvault secret set --vault-name <key vault name> --name "KEYVAULT-URI" --value "https://<keyvault name>.vault.azure.net/"
    az keyvault secret set --vault-name <key vault name> --name "AZURE-BLOB-CONTAINER-NAME-E2E-TEST" --value "e2e-tests"
    az keyvault secret set --vault-name <key vault name> --name "AZURE-OPENAI-SEED" --value "42"
    az keyvault secret set --vault-name <key vault name> --name "SESSION-MANAGER-URI" --value "https://<application gateway DNS name>.<region>.cloudapp.azure.com"
    az keyvault secret set --vault-name <key vault name> --name "CONVERSATION-DEPTH" --value "2"
    az keyvault secret set --vault-name <key vault name> --name "REDIS_HOST" --value <redis resource name>.redis.cache.windows.net
    az keyvault secret set --vault-name <key vault name> --name "REDIS_PORT" --value "6380"
    az keyvault secret set --vault-name <key vault name> --name "REDIS_PASSWORD" --value <password for the redis account>"
    ```


    >Note: For devloping and testing purpose, local emulator is recommended - [ComosDB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-develop-emulator?tabs=windows%2Ccsharp)

#### Azure OpenAI
1. To work with Azure OpenAI, developers need the `Azure AI Developer` role permission granted via Access control tab.
2. In order to access Azure OpenAI resource from other resources such as services running within AKS, one of of the following roles need to be assigned:
    1. Cognitive Services OpenAI User - view model deployments that can be used for inference
    2. Cognitive Services OpenAI Contributor - full access including ability to fine-tune and deploy models
3. Deploy various model deployment for Azure OpenAI Resource. This can be done by going to [oai.azure.com](https://oai.azure.com/portal), selecting the Azure OpenAI resource that was created in the previous step and clicking on Deployment. For the PoC we need two models deployed:
    - GPT 4o model: The solution utilizes the structured "Response Format" for the OpenAI service. Please ensure that a GPT-4o deployment is created with the "2024-08-06" version.
    ![GPT 4o](./docs/media/gpt4o-deployment.png)
    - Text embedding model
    ![Text Embedding ADA V2](./docs/media/text_embedding.png)

#### Azure AI Search
1. To work with Azure AI Search, developers need `Reader` and `Search Index Data Contributor` role permissions granted via Access control tab.
2. In order to access Azure AI Search from other resources such as services running within AKS, resources need `Reader` and one of the following roles:
    1. Search Index Data Reader - read access to index data
    2. Search Index Data Contributor - full access index
3. Verify there exists an index that matches the value in keyvault and `<repo root>\multimodalbot\src\skills\search\src\components\templates\rag.config.json`

#### Creating App registration for user Authentication with EntraID
1. Navigate to *Microsoft Entra ID* via the Azure Portal as at least a Cloud Application Administrator.
2. Select *App registrations* under the *Manage* tab and begin a new registration with an appropriate display name.
3. Upon successful creation of the resource, navigate to the app registration and make a note of the `Application ID` and `Directory ID`.
4. Navigate to the frontend web app. Add or update the environment variables `VITE_AUTH_CLIENT_ID` and `VITE_AUTH_AUTHORITY` to `<Application ID>` and `https://login.microsoftonline.com/<Directory ID>`, respectively.
5. Navigate to your app registration and Manage > Authentication. Click on "Add a Platform" and select "Single Page Application". Here you will have to enter your redirect URI. First URI to enter will be http://localhost:3000. This is for running the application locally. Click on "Condifigure" to save the changes.
6. Now you can add another URI pointing to the deployed frontend Web Application as part of the set up process, by click "Add URI" under the Single Page Application Section.


![app_registration_redirect_uri](./docs/media/app_registration_redirect_uri.png)

## Local Setup
<!-- From README -->
### Deployment Prerequisites

Before you begin, ensure you have the following prerequisites installed:

- [Python 3+](https://www.python.org/downloads/)
  - **Important**: Python and the pip package manager must be in the path in Windows for the setup scripts to work.
  - **Important**: Ensure you can run `python --version` from the console. You should see the version of python that you installed without any errors. On Ubuntu, you might need to run `sudo apt install python-is-python3` to link `python` to `python3`.
- [Node.js](https://nodejs.org/en/download/)
- [Git](https://git-scm.com/downloads)
- [PowerShell 7+ (pwsh)](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.5)
  - **Important**: Ensure you can run `pwsh.exe` from a PowerShell command. If this fails, you likely need to upgrade PowerShell.
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli//install-azd)
- On VSCode, Terminal login to Azure by following commands:
    ```
    azd auth login
    az login --use-device-code
    ```
- [Cosmos DB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-develop-emulator?tabs=windows%2Ccsharp&pivots=api-nosql)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

  > **NOTE**: Your Azure Account must have `Microsoft.Authorization/roleAssignments/write` permissions, such as [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator) or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner).

### Deploy Azure Resources

To run the solution end-to-end locally, several Azure resources are required, including:

- Azure Key Vault
- Azure OpenAI
- Azure AI Search
- Azure AI Service
- Document Intelligence
- Azure Cosmos DB (can be replaced with Cosmos DB Emulator for local setup)
- Azure Storage

For detailed deployment instructions, refer to the [Azure Setup](#azure-setup).

### CosmosDB Emulator

Since CosmosDB deployed by the script would be locked inside a vNet, its easier to deploy cosmsos DB emulator locally and use that. For doing so, follow steps below:

  1. Start the CosmosDB emulator locally.
  2. Add the following user account in the entities container:
      ```json
      {
          "user_name": "Anonymous",
          "description": "No user information.",
          "gender": "Other",
          "id": "anonymous",
          "partition_key": "user"
      }
      ```
      ![anonymous user account](./docs/media/default_user_profile.png)

### Redis
You should've installed Docker Desktop application as part of deployment prerequisites if not [do it now](https://www.docker.com/products/docker-desktop). Ensure it is running.

**NOTE:** Each microservice that relies on redis, will try to start the redis container locally if it is not already running. This is defined in the `.vscode\tasks.json` file


### Project Initialization

1. Clone this repo into a new folder and open the root folder in VS Code.

2. On VSCode terminal, login to Azure by running following commands:
    ```
    azd auth login
    az login --use-device-code
    ```

The project is divided into three main components:
1. Frontend
2. Core Microservices
3. Skills


#### Frontend
Frontend is a reactjs/typescript project.
Path: `<repo root>/Multimodalbot/src/frontent_rag`

To run the front end locally follow the steps below:

1. Make a copy of the `.env.template` file and paste it as `.env` file.
2. Update the .env file with the following env variables:

    ```
    VITE_BACKEND_URI=http://localhost:5000 # URI of Session Manager Microservice
    VITE_AUTH_REDIRECT_URI=http://localhost:3000 # URI of the frontend webapp
    VITE_CONFIGURATION_SERVICE_URI=http://localhost:5003 # URI of Configuration Microservice
    ```
  - Also, update VITE_AUTH_CLIENT_ID and VITE_AUTH_AUTHORITY with the actual values from webapp Azure resource that you created.

3. On the command prompt, in the `<repo root>/multimodalbot/src/frontend_rag` folder, run `npm install`.
4. Run `npm run dev`. This should start the frontend at port 3000. You can browse the frontend (web app) by going to `http://localhost:3000`.

**NOTE:**

- The webapp may not work end to end, until the microservices are running
-  Once deployed, use the web app configuration to update the VITE_BACKEND_URI to point to the deployed session manager endpoint like shown here:
![frontend webapp configuration](./docs/media/FrontEnd_config.png)

#### Core Microservices
1. **Setup Secrets and Environment Variables**:

    RAG Bot requires the following microservices:

    - `src/session_manager`
    - `src/data`
    - `src/config_hub`
    - `src/orchestrator_rag`
    - `src/skills/search`

    For each microservice copy the `src/*/.debug.env.template` and paste it in the same directory and rename it to `.debug.env`.

2. **Update the Environment Variables**:
-  Update the environment variables. Once not found in the `.debug.env` will be fetched from the KeyVault. So `KEYVAULT-URI` configuration is required. Make sure to check if microservice relies on redis by reviewing enronment variables and if so update the environment variables as follow:
    ```
    REDIS-HOST="localhost"
    REDIS-PORT="6379"
    REDIS-PASSWORD="redis_password"
    ```

3. **Review/Update Prompts**:
- Open `src/orchestrator_rag/app/static/static_orchestrator_prompts_config.yaml`. This file contains the model configuration definitions for the Azure OpenAI models that will be used. They define llm model parameters like `temperature`, `max_tokens`, etc., as well as the deployment name (`deployment_name`). The PoC code has been tested with `gpt-4o` `2024-08-06` version for both steps of orchestrations - fan out and final answer generation. Review and update the deployment name (`deployment_name`) to match those for the GPT model you've deployed. For models specifying a `total_max_tokens` param, set this value to the maximum number of tokens your deployed GPT model allows for a completions or embeddings request. This will allow the orchestrator service to know when prompts or embedding inputs need to be trimmed to avoid a token limit error.


4. **Run and debug services locally inside VS Code**:
- Open the folder `<repo root>\multimodalbot` in VSCode, you have two options:
  1. Click on `Run and Debug` to start an instance of each service locally:

      1. "Data service: Launch & Attach Server"
      2. "Configuration service: Launch & Attach Server"
      3. "Session Manager: Launch & Attach Server"
      4. "Orchestrator_Rag: Launch & Attach Server"
      5. "Search Skill: Launch & Attach Server"

  2. Click on `Run RAG Backend` to start each of these services in one click.

  > **Note**: As part of starting the service, VSCode will create python virtual environments in folder `.venv` and install all project-level dependencies into it. It will also try to start Redis container locally. Ensure that Docker Desktop is running; otherwise, these services may not start.


### Ingesting RAG data for testing
Details on how to use ingestion service to ingest RAG data can be found in the [ingestion service readme](../MultiModalBot/src/skills/ingestion/README_FINANCIAL.md) file.


### Testing and Evaluation

#### Integration testing

The solution includes a couple end-to-end tests to ensure that all microservices are functioning as expected. For more information on how to use the existing tests or add new ones, please refer to the [readme for integration test](./src/tests/int_test/README_RAG.md)

#### Simulated conversation based testing

Simulated conversations are needed to ensure the copilot is responding in an expected manner even when users' questions are coming in different formats and tones. Since humans can only test in limited ways, simulated conversation testing helps test on a wider scope of topics, styles, and tones.

More details on how to use simulated conversation based testing can be found in the [readme](../MultiModalBot/src/tests/e2e_test_agent/README.md) file

#### End-to-end Accuracy evaluation

Testing for accuracy (especially user-perceived accuracy or end-to-end accuracy of the response produced by the copilot) is crucial for the successful adoption of the copilot by its users. Accuracy testing is also very iterative as improving accuracy is an iterative process. It could involve finding better ways to ingest data, chunk and index them, improving how search is configured, how user queries are restated for efficient searching, and how the final answer is curated and presented to the user.

To perform accuracy testing, one needs ground truth (question/answer pairs). This dataset is then used against the copilot to produce responses, and the responses are compared against the ground truth. To make evaluations easy, the team invested in building out an evaluation tool.
More details on how to use the tool can be found in the [evaluation tools readme](./src/evals/README.md)


### Instrumentation and application logs
Instrumentation and logging are very important to be able to trace and debug issues on the server. They are also important to log key metrics that can then be used for measuring various optimization techniques. More details on this topic can be found in the [logging document](./docs/logging.md)


## Build Your Own Copilot
You can easily modify system based on your needs to create your own copilot, from adding your own data for ingestion to adding skills.
- Ingestion Service:
  You can bring your own data with your own fields. For this just make sure to update storage container so that index has desired fields. Also update the payload format (currently DocumentPayload) to align with your data structure.

  Modify the enrichment processes as needed to generate AI-powered metadata tailored to your dataset. This could include custom attributes, descriptions, or other relevant fields specific to your data domain.

  For both payload format and enrichment make sure to apply changes to this [file](./src/skills/ingestion/models/api_models.py) to define your data structure and payload format for usage throughout the code. Update ingestion service so that it uses your data.

  For details on how to bring your own data to the solution, following guidance [here](src/skills/ingestion/README_FINANCIAL.md).

- Updating or Adding Skills:

  Customize Skills:
  To adapt the solution to your specific requirements, you can modify or add skills tailored to your use case. This customization ensures the bot provides precise, context-aware results that align with your domain.

  Update the Orchestrator Service:
  Ensure the orchestrator service is updated to effectively consume the newly added or modified skills.

  Configure Skill Prompts:
  Adjust the prompts in the prompt_config.yaml file to refine the behavior and output of the skills. You can also configure the AI model used by each skill in this file to suit your desired performance and accuracy.

For common issues and troubleshooting, please refer to our [FAQ guide.](FAQ.md)


## Guidance

### Region Availability

This template uses `gpt-4o` which may not be available in all Azure regions. Check for [up-to-date region availability](https://learn.microsoft.com/azure/ai-services/openai/concepts/models#standard-deployment-model-availability) and select a region during deployment accordingly

### Costs

You can estimate the cost of this project's architecture by leveraging [Azure's pricing calculator](https://azure.microsoft.com/pricing/calculator/)

After setting up the solution end-to-end and running a few queries, you can analyze the costs by reviewing logs in Application Insights. These logs provide insights into:

**Azure OpenAI Calls:** Track the number of API calls and the corresponding token usage per request.
**Query Completion Time:** Measure the time taken for each query to complete.

For detailed logging information, refer to the [logging.md](docs/logging.md) file.

To optimize costs, consider adjusting the models used in your solution. Smaller models are more cost-effective but may impact accuracy, so it's important to find the right balance based on your specific requirements.


### Security

To ensure best practices in your repo we recommend anyone creating applications based on our solution ensure that the [Github secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning) setting is enabled in your repos.


## Additional Resources

- [Azure Cosmos DB](https://azure.microsoft.com/en-us/services/cosmos-db/)
- [Redis](https://redis.io/docs/latest/)
- [Azure AI Services](https://learn.microsoft.com/en-us/azure/ai-services/)
- [Azure Application Insights](https://azure.microsoft.com/en-us/services/monitor/)
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Authentication in SPA](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-single-page-app-react-sign-in)