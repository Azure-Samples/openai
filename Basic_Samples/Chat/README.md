# Introduction

This repository contains samples demonstrating how to use ChatGPT via Python SDK.

## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

### Microsoft Azure Endpoints
In order to use the Open AI library or REST API with Microsoft Azure endpoints, you need to set CHATGPT_MODEL, OPENAI_API_BASE & OPENAI_API_VERSION in _config.json_ file. 

```js
{
    "CHATGPT_MODEL":"<ChatGPT Model Name>",
    "OPENAI_API_BASE":"https://<Your Azure Resource Name>.openai.azure.com",
    "OPENAI_API_VERSION":"<OpenAI API Version>"
}
``` 

### For getting started:
- Add "OPENAI_API_KEY" as variable name and \<Your API Key Value\> as variable value in the environment variables.
<br>
One can get the OPENAI_API_KEY value from the Azure Portal. Go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for one of the "Keys" values.
 <br>
 Steps to set the key in the environment variables:        

      WINDOWS Users: 
         setx OPENAI_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"

      MACOS/LINUX Users: 
         export OPENAI_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"

- To find your "OPENAI_API_BASE" go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for the "Endpoint" value.

- For the sample scenario, one can use "gpt-35-turbo" as "CHATGPT_MODEL" in _config_ file. The "gpt-35-turbo" is the deployment name you chose when you want to deploy the ChatGPT or GPT-4 model.
   ```
   {
      "CHATGPT_MODEL":"gpt-35-turbo",
      "OPENAI_API_BASE":"https://<Your Azure Resource Name>.openai.azure.com",
      "OPENAI_API_VERSION":"2023-03-15-preview"
   }
   ```
- The currently available API version for Chat Completions is "2023-03-15-preview".

Learn more about Azure OpenAI Chat Completions [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/chatgpt?pivots=programming-language-chat-completions).


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


