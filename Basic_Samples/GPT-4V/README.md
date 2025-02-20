
# Introduction

This repository contains a collection of Jupyter notebooks demonstrating various use cases for interacting with the GPT-4V API, along with samples demonstrating how to use GPT-4V for Chat Completions via REST API. These examples provide practical guidance and accelerators for developers integrating GPT-4V functionalities in their applications.

## Contents
| Notebook | Description | Type |
|----------|-------------|-------|
| [Basic Image in GPT-4V](basic_chatcompletions_example_restapi.ipynb) | Processing a single image input with GPT-4V. | Image |
| [Handling Multiple Images in GPT-4V](mutiple_images_chatcompletions_example_restapi.ipynb) | Managing multiple image inputs in GPT-4V. | Image |
| [Enhancing GPT-4V with RAG and Custom Data](RAG_chatcompletions_example_restapi.ipynb) |  Enhancing capabilities by bringing custom data to augment image inputs in GPT-4V. | Image |
| [Enhancing GPT-4V with Grounding Techniques](enhancement_grounding_chatcompletions_example_restapi.ipynb) | Applying grounding techniques to image inputs in GPT-4V. | Image |
| [Enhancing GPT-4V with OCR Technique](enhancement_OCR_chatcompletions_example_restapi.ipynb) | Incorporating Optical Character Recognition (OCR) with image inputs in GPT-4V. | Image |
| [Basic Video QnA in GPT-4V](video_chatcompletions_example_restapi.ipynb) | Conducting Q&A with video inputs in GPT-4V. | Video |
| [Video Chunk Processing Sequentially in GPT-4V](video_chunk_chatcompletions_example_restapi.ipynb) | Sequential processing of video chunks in GPT-4V. | Video |


## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

### Microsoft Azure Endpoints
In order to use REST API with Microsoft Azure endpoints, you need to set a series of configurations such as GPT-4V_DEPLOYMENT_NAME, OPENAI_API_BASE, OPENAI_API_VERSION in _config.json_ file. 

```js
{
    "GPT-4V_DEPLOYMENT_NAME":"<GPT-4V Deployment Name>",
    "OPENAI_API_BASE":"https://<Your Azure Resource Name>.openai.azure.com",
    "OPENAI_API_VERSION":"<OpenAI API Version>",

    "VISION_API_ENDPOINT": "https://<Your Azure Vision Resource Name>.cognitiveservices.azure.com"

    "AZURE_SEARCH_SERVICE_ENDPOINT": "https://<Your Azure Search Resource Name>.search.windows.net",
    "AZURE_SEARCH_INDEX_NAME": "<Your Azure Search Index Name>",

    "VIDEO_SAS_URL": "<Your Azure Blob Storage SAS URL>",
    "VIDEO_INDEX_NAME": "<Your Azure Video Index Name>",
    "VIDEO_INDEX_ID": "<Your Azure Video Index ID>"
}
``` 

### For getting started:
- Add "OPENAI_API_KEY", "VISION_API_KEY", and "AZURE_SEARCH_QUERY_KEY" (optional) as variable name and \<Your API Key Value\>, \<Your VISION Key Value\>, and \<Your SEARCH Query Key Value\> (optional) as variable value in the environment variables.
<br>
One can get the OPENAI_API_KEY, VISION_API_KEY, and AZURE_SEARCH_QUERY_KEY values from the Azure Portal. Go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for one of the "Keys" values.
 <br>
      
      WINDOWS Users: 
         setx OPENAI_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"
         setx VISION_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"
         setx AZURE_SEARCH_QUERY_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"

      MACOS/LINUX Users: 
         export OPENAI_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"
         export VISION_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"
         export AZURE_SEARCH_QUERY_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"

- To find your "OPENAI_API_BASE", "VISION_API_ENDPOINT", and "AZURE_SEARCH_SERVICE_ENDPOINT" go to https://portal.azure.com, find your resource and then under "Resource Management" -> "Keys and Endpoints" look for the "Endpoint" value.

Learn more about Azure OpenAI Service REST API [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference).


## Requirements
Python 3.8+ <br>
Jupyter Notebook 6.5.2


## Usage

Each notebook is self-contained and includes instructions specific to its scenario. Simply open a notebook in Jupyter and follow the steps outlined within it.

## Shared Functions

For convenience, commonly used functions across these notebooks are consolidated in [shared_functions.ipynb](shared_functions.ipynb). Import these functions in any notebook as needed.


## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
