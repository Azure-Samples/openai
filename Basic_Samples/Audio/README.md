# Introduction

This repository contains samples demonstrating how to use the Audio Whisper models via Python SDK.

## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

### Microsoft Azure Endpoints
In order to use the Open AI library with Microsoft Azure endpoints, you need to set OPENAI_API_BASE, OPENAI_API_KEY, and WHISPER_DEPLOYMENT_ID in the `.env` file. 

```txt
OPENAI_API_BASE=https://<resource>.openai.azure.com/
OPENAI_API_KEY=<api-key>
WHISPER_DEPLOYMENT_ID=<whisper-deployment>
``` 

### For getting started:
- Add "OPENAI_API_KEY" as variable name and \<Your API Key Value\> as variable value in the environment variables.
<br>
One can get the OPENAI_API_KEY value from the Azure Portal. Go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for one of the "Keys" values.
 <br>

- To find your "OPENAI_API_BASE" go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for the "Endpoint" value.

- For the sample scenario, you can set your deployment ID to "WHISPER_DEPLOYMENT_ID" in the .env file. The deployment ID is the name you chose when you deployed the Whisper model.

- The currently available API version for Audio transcription and translation is "2023-09-01-preview".

Learn more about Azure OpenAI Audio [here](https://learn.microsoft.com/azure/ai-services/openai/whisper-quickstart?tabs=command-line).


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


