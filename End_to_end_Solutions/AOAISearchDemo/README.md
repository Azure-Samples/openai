# ChatGPT + Enterprise data with Azure OpenAI and Cognitive Search

This sample demonstrates a few approaches for creating ChatGPT-like experiences over your own data using the Retrieval Augmented Generation pattern. It uses Azure OpenAI Service to access the GPT model - gpt-4(8k tokens), Azure Cognitive Search for data indexing and retrieval of unstructured content (pdf files) and SQL Server for retrieving data from SQL server tables.

The repo includes sample data so it's ready to try end to end. In this sample application we used two sources of data:
>
> 1. Cognitive Search is ingested with  publicly available documentation on [Microsoft Surface devices](https://learn.microsoft.com/en-us/surface/get-started),
> 2. SQL server is loaded with some sample product availability, sales and merchant information about certain Surface devices

The experience allows users to ask questions about the Surface Devices specifications, troubleshooting help, warranty as well as sales, availability, and trend related questions. 

There are two pre-recorded voiceovers that shows how enterprises can use this architecture for their different users/audiences. The demo uses two different personas:
> 1. Emma is marketing lead [demo](./docs/Emma%20Miller_with%20voice.mp4)
> 2. Dave is regional sales manager [demo](./docs/Dave%20Huang_with%20voice.mp4)

![RAG Architecture](docs/appcomponents.png)

## Features

* Chat on different data sources (structured and unstructured)
* Maintain context when chatting across data sources
* Explores various options to help users evaluate the trustworthiness of responses with citations, tracking of source content, etc.
* Shows approaches for data preparation, prompt construction, and orchestration of interaction between model (GPT) and retriever (Cognitive Search and SQL)
* Settings directly in the UX to tweak the behavior and experiment with options
* Simulation of securing resources by user/role [RBAC](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview). RBAC is built into Azure Resource Manager, however for the demo we have simulated user roles, so we have managed the intersection of role, scope and role assignments in a separate storage. Enterprise can leverage the same concept if bringing in external resources or leverage the built in RBAC if they have all their resources in Azure.
* Handling failures gracefully and ability to retry failed queries against other data sources
* Handling token limitations
* Using fine-tuned model for classification in the orchestrator
* Using instrumentation for debugging and also for driving certain usage reports from the logs

![Chat screen](docs/chatscreen.png)

## Getting Started

> **IMPORTANT:** In order to deploy and run this example, you'll need an **Azure subscription with access enabled for the Azure OpenAI service**. You can request access [here](https://aka.ms/oaiapply). You can also visit [here](https://azure.microsoft.com/free/cognitive-search/) to get some free Azure credits to get you started.

> **AZURE RESOURCE COSTS** by default this sample will create various Azure resources like: Azure App Service, Azure Cognitive Search, Azure SQL Server, Azure KeyVault, Azure Cosmos DB and Form Recognizer resource that has cost associated with them. You can switch them to free versions if you want to avoid this cost by changing the parameters file under the infra folder (though there are some limits to consider; for example, you can have up to 1 free Cognitive Search resource per subscription, and the free Form Recognizer resource only analyzes the first 2 pages of each document.)

### Prerequisites

#### To Run Locally

- [Azure Developer CLI](https://aka.ms/azure-dev/install)
* [Python 3+](https://www.python.org/downloads/)
  * **Important**: Python and the pip package manager must be in the path in Windows for the setup scripts to work.
  * **Important**: Ensure you can run `python --version` from console. On Ubuntu, you might need to run `sudo apt install python-is-python3` to link `python` to `python3`.
* [Node.js](https://nodejs.org/en/download/)
* [Git](https://git-scm.com/downloads)
* [Powershell 7+ (pwsh)](https://github.com/powershell/powershell) - For Windows users only.
  * **Important**: Ensure you can run `pwsh.exe` from a PowerShell command. If this fails, you likely need to upgrade PowerShell.

>NOTE: Your Azure Account must have `Microsoft.Authorization/roleAssignments/write` permissions, such as [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator) or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner).  

### Installation

#### Project Initialization

1. Create a new folder and switch to it in the terminal
1. Run `azd login`
1. Run `azd init -t AOAISearchDemo`
    * For the target location, the regions that currently support the models used in this sample are **East US** or **South Central US**. For an up-to-date list of regions and models, check [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models)

#### Starting from scratch

Execute the following command, if you don't have any pre-existing Azure services and want to start from a fresh deployment.

1. Run `azd up`. This will:

* Start a deployment that will provision the necessary Azure resources needed for the sample to run, as well as upload secrets to Azure Keyvault and save environment variables in your azd env needed to access those resources.
  * **Note**: You must make sure every deployment runs successfully. A failed deployment could lead to missing resources, secrets or env variables that will be needed downstream.
* Prepare and upload the data needed for the sample to run, including building the search index based on the files found in the `./data` folder and pre-populating some Cosmos DB containers with starter data for user profiles, access rules, resources, etc.
* Install needed Node.js dependencies and build the app's front-end.
* Deploy the services needed for the app to run to Azure. This will include a data-management micro-service as well as the backend service that the front-end UI will communicate with.

1. Once this is all done, the application is successfully deployed and you will see 2 URLs printed on the console.  Click the backend URL to interact with the application in your browser.

It will look like the following:

!['Output from running azd up'](docs/endpoint.png)

> NOTE: It may take a minute for the application to be fully deployed. If you see a "Python Developer" welcome screen, then wait a minute and refresh the page.

#### Use existing resources

If you wish to use your own Azure Open AI resource, you can

1. Add to KeyVault secret `AZURE-OPENAI-GPT4-SERVICE {Name of existing OpenAI service where GPT4 model has been deployed}`
1. Add to KeyVault secret `AZURE-OPENAI-GPT4-DEPLOYMENT {Name of GPT4 deployed model}`
1. Add to KeyVault secret `AZURE-OPENAI-RESOURCE-GROUP {Name of existing resource group that OpenAI service is provisioned to}`
1. Add to KeyVault secret `AZURE-OPENAI-CLASSIFIER-SERVICE {Name of existing OpenAI service where classifier is deployed}`.
1. Add to KeyVault secret `AZURE-OPENAI-CLASSIFIER-DEPLOYMENT {Name of existing classifier deployment name}`.
1. Uncomment the classifier deployment inside the main [Bicep template](./infra/main.bicep). By default, no GPT models are deployed.
1. Run `azd up`

> NOTE: You can also use existing Search and Storage Accounts.  See `./infra/main.parameters.json` for list of environment variables to pass to `azd env set` to configure those existing resources.

#### Deploying or re-deploying a local clone of the repo

* Simply run `azd up`
* Once all the resources have been deployed. Update the data and backend service configurations to include KeyVault URI.
!['App Settings Configuration'](docs/app_settings_configuration.png)

### Running locally

1. Run `azd login`
2. Change dir to `app`
3. Run `./start.ps1` or `./start.sh` or run the VS Code Launch - "Frontend: build", "Data service: Launch & Attach Server" and "Backend: Launch & Attach Server" to start the project locally.

#### Sharing Environments

Run the following if you want to give someone else access to completely deployed and existing environment.

1. Install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
1. Run `azd init -t AOAISearchDemo`
1. Run `azd env refresh -e {environment name}` - Note that they will need the azd environment name, subscription Id, and location to run this command - you can find those values in your `./azure/{env name}/.env` file.  This will populate their azd environment's .env file with all the settings needed to run the app locally.
1. Run `pwsh ./scripts/roles.ps1` - This will assign all of the necessary roles to the user so they can run the app locally.  If they do not have the necessary permission to create roles in the subscription, then you may need to run this script for them. Just be sure to set the `AZURE_PRINCIPAL_ID` environment variable in the azd .env file or in the active shell to their Azure Id, which they can get with `az account show`.

### Quickstart

* In Azure: navigate to the Backend Azure WebApp deployed by azd. The URL is printed out when azd completes (as "Endpoint"), or you can find it in the Azure portal.
* Running locally: navigate to 127.0.0.1:5000

Once in the web app:

* Try different topics in chat or Q&A context. For chat, try follow up questions, clarifications, ask to simplify or elaborate on answer, etc.
* Explore citations and sources
* Click on "settings" to try distinct roles, options, etc.

## Fine-tuning

You can find helpful resources on how to fine-tune a model on the Azure OpenAI website. We have also provided synthetic datasets we used for this demo application in the data folder for users who want to try it out.

* [Learn how to prepare your dataset for fine-tuning](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/prepare-dataset)
* [Learn how to customize a model for your application](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/fine-tuning?pivots=programming-language-studio)

## Resources

* [Revolutionize your Enterprise Data with ChatGPT: Next-gen Apps w/ Azure OpenAI and Cognitive Search](https://aka.ms/entgptsearchblog)
* [Azure Cognitive Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
* [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/overview)

### Note
>
>Note: The PDF documents used in this demo contain information generated using a language model (Azure OpenAI Service). The information contained in these documents is only for demonstration purposes and does not reflect the opinions or beliefs of Microsoft. Microsoft makes no representations or warranties of any kind, expressed or implied, about the completeness, accuracy, reliability, suitability or availability with respect to the information contained in this document. All rights reserved to Microsoft.

## FAQ

***Question***: Why do we need to break up the PDFs into chunks when Azure Cognitive Search supports searching large documents?

***Answer***: Chunking allows us to limit the amount of information we send to OpenAI due to token limits. By breaking up the content, it allows us to easily find potential chunks of text that we can inject into OpenAI. This demo uses page-based chunking where each chunk is a page. For the purposes of this content, page-based chunking produced good results as it has enough context. Additional chunking strategies were also considered and you can find details of those in the [search optimization doc](docs/search_optimization.md)

***Question***: Have you considered other development frameworks like LangChain

***Answer***: Yes we did do a study of LangChain and have documented our architecture and other considerations in the [architecture considerations doc](docs/architecture_considerations.md).

***Question***: Do you have any suggestions for getting the right results from the content

***Answer***: Yes, we did this with two approaches:

1. There is a classifier upfront. Every user utterance goes thru this classifier to ensure demo can answer those user questions for which it has content for and gracefully answer what it can't do.
2. System prompts were also updated to ensure the response are generated based on the context and previous history. In addition, for natural language to SQL prompt, we also included instructions to only generate SELECT queries and restrict from making any updates to the data or schema.

***Question***: Are there examples of usage reports derived from the logging

***Answer***: Yes, as part of the development of the application, we included some basic logging to capture what is happening around a user conversation. Application Insights was used as the logging backend. The [log reports](docs/log_reports.md) document has some sample KQL queries and reports based on these logs

### Troubleshooting

If you see this error while running `azd deploy`: `read /tmp/azd1992237260/backend_env/lib64: is a directory`, then delete the `./app/backend/backend_env folder` and re-run the `azd deploy` command.  This issue is being tracked here: <https://github.com/Azure/azure-dev/issues/1237>
