# Setup to use Azure Active Directory Authentication

This document describes how to set up your machine to use Azure Active Directory (AAD) authentication to call the Azure OpenAI (AOAI) API.  

Follow the steps below to test access using the CLI.  The example uses `bash` on WSL2.  The steps are similar for other shells and operating systems.

## Prerequisites

1. Azure CLI.  You need to have the Azure CLI installed on your machine.  See [Install the Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli).
2. Azure Identity Python package.  You need to have the Azure Identity Python package installed on your machine for the Python examples.
    * [Setup Python environment](setup_python_env.md) describes how to set up a Python virtual environment and install the required package.
    * For details on the Azure Identity package, see [Azure Identity for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python).
3. For the CLI examples, you need to have the `jq` command installed on your machine.  See [jq](https://stedolan.github.io/jq/).


## Storing your API endpoint URL
We assume below that you have your endpoint base URL in the `OPENAI_API_BASE` environment variable.  It doesn't matter what the environment variable is called for use in the CLI, but `OPENAI_API_BASE` is used by the OpenAI Python SDK.  For example, if your endpoint base URL is `https://endpointname.openai.azure.com`, then you would set the environment variable as follows:

```bash
export OPENAI_API_BASE=https://endpointname.openai.azure.com
```


## Use Azure CLI to authenticate
The Azure CLI provides the `az login` command to authenticate with Azure Active Directory (AAD).  This command will try to open a browser window to authenticate with AAD.  If it cannot open a browser window, follow the instructions using the code it gives you.  After authentication, the CLI will store the access token in the local machine's credential store.  The CLI will use the access token to authenticate with the API.
```
az login
```

## Get Authentication Token
Once you have signed, get the authentication token as follows:
```
export accessToken=$(az account get-access-token --resource https://cognitiveservices.azure.com | jq -r .accessToken)
```

Keep this token secure!  Do not share it with anyone.  Do not check it into source control.

## Test the API

Replace `<ENGINE_NAME>` below with your engine name.  The engine name is the name that your team administrator used when creating the model deployment.
```bash
curl ${OPENAI_API_BASE%/}/openai/deployments/<ENGINE_NAME>/completions?api-version=2022-06-01-preview \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $accessToken" \
-d '{ "prompt": "Tell me a funny story." }'
```

If you get an Access Denied error (e.g., `401 Unauthorized`), then you need to check the following:
1. You signed in with `az login` recently and have a valid access token.  Tokens expire after a period.
2. You have the correct API endpoint URL in the `OPENAI_API_BASE` environment variable.
3. You have the correct engine name in the URL.
4. You have the correct API version in the URL.

If the above are correct, contact your team's API administrator to check your access.

## Using Visual Studio Code

IMPORTANT: You should make sure to `az login` in your environment before using VS Code, and launch VS Code from a shell where `az login` is completed.  If you use WSL, you may need to do `az login` in both WSL and Windows.  If things work in raw command line but fail in VS Code, then you may be launching VS Code in a context where you are not AZ logged in.

In order to use AAD authentication with Visual Studio Code (VS Code), you should install the [Azure Account](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-account) extension.  This extension will use the access token stored in the local machine's credential store to authenticate with the API.

The Azure Identity Python [documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#authenticate-during-local-development) has good coverage on how to use AAD authentication with VS Code including current workarounds if any.

## Tested Versions
This repo was tested on October 23, 2022 using:
```
$ az --version
azure-cli                         2.41.0

core                              2.41.0
telemetry                          1.0.8

Extensions:
ml                               2.0.1a3

Dependencies:
msal                            1.20.0b1
azure-mgmt-resource             21.1.0b1
```
