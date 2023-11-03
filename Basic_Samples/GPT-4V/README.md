
# Introduction

This repository contains samples demonstrating how to use GPT-4V for Chat Completions via REST API.

## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

### Microsoft Azure Endpoints
In order to use REST API with Microsoft Azure endpoints, you need to set GPT-4V_MODEL, OPENAI_API_BASE, OPENAI_API_VERSION & VISION_API_ENDPOINT in _config.json_ file. 

```js
{
    "GPT-4V_MODEL":"<GPT-4V Model Name>",
    "OPENAI_API_BASE":"https://<Your Azure Resource Name>.openai.azure.com",
    "OPENAI_API_VERSION":"<OpenAI API Version>",

    "VISION_API_ENDPOINT": "https://<Your Azure Vision Resource Name>.cognitiveservices.azure.com"
}
``` 

### For getting started:
- Add "OPENAI_API_KEY" and "VISION_API_KEY" (optional) as variable name and \<Your API Key Value\> and \<Your VISION Key Value\> (optional) as variable value in the environment variables.
<br>
One can get the OPENAI_API_KEY and VISION_API_KEY values from the Azure Portal. Go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for one of the "Keys" values.
 <br>
      
      WINDOWS Users: 
         setx OPENAI_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"
		 setx VISION_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"

      MACOS/LINUX Users: 
         export OPENAI_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"
         export VISION_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"

- To find your "OPENAI_API_BASE" and "VISION_API_ENDPOINT" go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for the "Endpoint" value.

Learn more about Azure OpenAI Service REST API [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference).


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
