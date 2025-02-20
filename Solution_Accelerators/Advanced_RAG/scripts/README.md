# Overview
This document will guide you through the process of loading data present in the form of pdf's/txt's into an Azure AI Search resource.

## Prerequisite
* The following resources have been deployed via the automated `azd up` approach (refer README.md under infra module) or manually created:
    * Azure Blob Storage
    * Azure AI Search
    * Azure AI Document Intelligence
    * Azure OpenAI with embedding model - recommended to use `text-embedding-ada-002` or above
* [Python 3.10+](https://www.python.org/downloads/)
  * **Important**: Python and the pip package manager must be in the path in Windows for the setup scripts to work.
  * **Important**: Ensure you can run `python --version` from console. On Ubuntu, you might need to run `sudo apt install python-is-python3` to link `python` to `python3`
* [PowerShell 7.4+ (pwsh)](https://github.com/powershell/powershell)

## Script Execution
1. Set the variables in `prepdata.ps1` with respective service names and credentials.
1. Create a folder named `data` and add files that need to be ingested. 
1. Launch a powershell window and run the script using the command `.\prepdata.ps1`.