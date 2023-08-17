# Introduction
This repository contains samples demonstrating how to use functions to extend the current capabilities of GPT Models.

## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

### Microsoft Azure Endpoints
In order to use the Open AI library or REST API with Microsoft Azure endpoints, you need to set DEPLOYMENT_ID, OPENAI_API_BASE & OPENAI_API_VERSION in the _config.json_ file. 

```json
{
    "DEPLOYMENT_ID":"<Model Deployment Name>",
    "OPENAI_API_BASE":"https://<Your Azure Resource Name>.openai.azure.com",
    "OPENAI_API_VERSION":"<OpenAI API Version>",

    // Only required for the functions_with_azure_search.ipynb notebook
    "SEARCH_SERVICE_ENDPOINT": "https://<Your Search Service Name>.search.windows.net",
    "SEARCH_INDEX_NAME": "recipes-vectors",
    "SEARCH_ADMIN_KEY": ""
}
``` 

### For getting started:
- Add "OPENAI_API_KEY" as variable name and \<Your API Key Value\> as variable value in the environment variables.
<br>
One can get the OPENAI_API_KEY value from the Azure Portal. Go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for one of the "Keys" values.
 <br>
      
      WINDOWS Users: 
         setx OPENAI_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"

      MACOS/LINUX Users: 
         export OPENAI_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"

- To find your "DEPLOYMENT_ID" go to the deployments page of the Azure AI Studio. Create a deployment if one does not already exist.
One can start with using your model name as "gpt-35-turbo-0613" or "gpt-4."

- To find your "OPENAI_API_BASE" go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for the "Endpoint" value.
- Current, function calling can only be used with the "2023-07-01-preview" API version. Check out versions [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference).


## Requirements
Python 3.8+ <br>
Jupyter Notebook 6.5.2

<br>

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.