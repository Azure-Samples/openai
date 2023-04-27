# Azure OpenAI API Service Samples AAD integration

## Using the AOAI Service API

You can call the API in the following ways:
1. Directly call the AOAI Service REST API using your method of choice.  This includes and is not limited to:
    * Python `requests`, JavaScript, C#, etc.
    * `curl` from command line 
    * Postman : Use only local installed versions of programs like Postman, not cloud hosted versions.  You should check status of 3rd party tools carefully so that they are not logging confidential information.
2. Call the AOAI Service API using the OpenAI Python SDK

To call the API, you need to authenticate with Azure Active Directory (AAD).

## Table of Contents

|Topic| 
|--|
| [Setup to use AAD and test with CLI](setup_aad.md) | 
| [Setup Python virtual environment](setup_python_env.md) | 
| [Sample Python notebook for OpenAI SDK](aad_integration_example_sdk.ipynb) |  
| [Sample Python notebook for REST](aad_integration_example_restapi.ipynb) |

