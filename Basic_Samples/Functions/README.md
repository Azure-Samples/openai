# Introduction
This repository contains samples demonstrating how to use functions to extend the current capabilities of GPT Models.

## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

### Microsoft Azure Endpoints
In order to use the OpenAI library or REST API with Microsoft Azure endpoints, you need to set your `AZURE_OPENAI_ENDPOINT` in the `config.json` file. We've prepopulated the `MODEL_NAME` and `OPENAI_API_VERSION` variables for you in the `config.json` file with default values. You can change these values if you like.

```json
{
    "DEPLOYMENT_ID":"<Model Deployment Name>",
    "AZURE_OPENAI_ENDPOINT":"https://<Your Azure Resource Name>.openai.azure.com",
    "OPENAI_API_VERSION":"<OpenAI API Version>",

    // Only required for the functions_with_azure_search.ipynb notebook
    "SEARCH_SERVICE_ENDPOINT": "https://<Your Search Service Name>.search.windows.net",
    "SEARCH_INDEX_NAME": "recipes-vectors",
    "SEARCH_ADMIN_KEY": ""
}
``` 

### For getting started:
- Add `OPENAI_API_KEY` as variable name and \<Your API Key Value\> as variable value in the environment variables.
<br>
One can get the OPENAI_API_KEY value from the Azure Portal. Go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for one of the "Keys" values.
 <br>
      
      WINDOWS Users: 
         setx OPENAI_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"

      MACOS/LINUX Users: 
         export OPENAI_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"

- To find your `AZURE_OPENAI_ENDPOINT` go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for the "Endpoint" value.



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