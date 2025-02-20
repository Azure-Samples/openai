
  > [Note]
  > **This repository is a work in progress and will be updated frequently with changes.**

# Azure OpenAI Service Samples

This repo is a compilation of useful [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service/) resources and code samples to help you get started and accelerate your technology adoption journey.

The Azure OpenAI service provides REST API access to OpenAI's powerful language models on the Azure cloud. These models can be easily adapted to your specific task including but not limited to content generation, summarization, semantic search, and natural language to code translation. Users can access the service through REST APIs, Python SDK, .NET SDK, or our web-based interface in the Azure AI Foundry.

## Get started

### Prerequisites

- **Azure Account** - If you're new to Azure, get an Azure account for [free](https://aka.ms/free) and you'll get some free Azure credits to get started.
- **Azure subscription with access enabled for the Azure OpenAI Service** - For more details, see the [Azure OpenAI Service documentation on how to get access](https://learn.microsoft.com/azure/ai-services/openai/overview#how-do-i-get-access-to-azure-openai). 
- **Azure OpenAI resource** - For these samples, you'll need to deploy models like GPT-3.5 Turbo, GPT 4, DALL-E, and Whisper. See the Azure OpenAI Service documentation for more details on [deploying models](https://learn.microsoft.com/azure/ai-services/openai/how-to/create-resource?pivots=web-portal) and [model availability](https://learn.microsoft.com/azure/ai-services/openai/concepts/models).

### Project setup
The repo includes many end to end solutions and solution accelerators with sample data and detailed installation instructions. Follow the instructions provided with these solutions to get going.


### Navigating the repo
- [**eCommerce Solution Accelerator**](./Solution_Accelerators/Retail/README.md): This solution demonstrates building an eCommerce copilot with a multimodal, concierge-like shopping experience. It leverages Azure OpenAI Service and Azure AI Search to index and retrieve multimodal content, enabling product discovery through text, images, and personalized recommendations.
- [**Advanced RAG for Financial Domain**](./Solution_Accelerators/Advanced_RAG/README.md): This is a solution accelerator that supports advanced techniques for ingesting, formatting and intent extraction from structured and non-structured data and querying the data through simple web interface to achieve improved accuracy and performance rates than baseline RAG.
- [**Basic samples**](./Basic_Samples/README.md): These are small code samples and snippets which complete small sets of actions and can be integrated into the user code.
- [**End to end solutions**](./End_to_end_Solutions/README.md): These are complete solutions for some use cases and industry scenarios. These include appropriate workflows and reference architectures, which can be easily customized and built into full scale production systems.

## Additional Resources

### Documentation

* [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
* [Underlying models that power the Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models)
* [Apply for access to Azure OpenAI Service.](https://aka.ms/oaiapply) Access is currently limited as we navigate high demand, upcoming product improvements, and  [Microsoft’s commitment to responsible AI](https://www.microsoft.com/ai/responsible-ai?activetab=pivot1:primaryr6). More specific information is included in the application form. We appreciate your patience as we work to responsibly enable broader access to the Azure OpenAI Service. Once approved for use, customers can log in to the Azure portal to create an Azure OpenAI Service resource and then get started either in our Studio website or via code:
  - [How to create an Azure OpenAI Service resource](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal)
  - [Quickstart: how to get started generating text](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?pivots=programming-language-studi)
* Read the statement on responsible use of OpenAI [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/overview#responsible-ai). Also, visit the [Responsible AI](https://www.microsoft.com/en-us/ai/responsible-ai?rtc=1&activetab=pivot1:primaryr6) site to learn more about Microsoft’s principles for responsible AI use.

### The Azure OpenAI Service promise
Azure OpenAI Service gives customers advanced language AI with OpenAI GPT-3, Codex, and DALL-E models with the security and enterprise promise of Azure. Azure OpenAI co-develops the APIs with OpenAI, ensuring compatibility and a smooth transition from one to the other.

With Azure OpenAI Service, customers get the security capabilities of Microsoft Azure while running the same models as OpenAI. Azure OpenAI Service offers private networking, regional availability, and responsible AI content filtering.

### Important concepts and terminology

#### Prompts & Completions
The completions endpoint is the core component of the API service. This API provides access to the model's text-in, text-out interface. Users simply need to provide an input prompt containing the English text command, and the model will generate a text completion.

Here's an example of a simple prompt and completion:

> Prompt:`         """         count to 5 in a for loop         """        `

> Completion:`        for i in range(1, 6):             print(i)        `

#### Tokens
The Azure OpenAI Service and OpenAI Enterprise process text by breaking it down into tokens. Tokens can be words or just chunks of characters. For example, the word “hamburger” gets broken up into the tokens “ham”, “bur” and “ger”, while a short and common word like “pear” is a single token. Many tokens start with a whitespace, for example “ hello” and “ bye”.

The total number of tokens processed in a given request depends on the length of your input, output and request parameters. The quantity of tokens being processed will also affect your response latency and throughput for the models.

#### Resources
The Azure OpenAI Service is a new product offering on Azure. You can get started with the Azure OpenAI Service the same way as any other Azure product where you [create a resource](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal), or instance of the service, in your Azure Subscription.

#### Deployments
Once you create an Azure OpenAI Service Resource, you must deploy a model before you can start making API calls and generating text. This action can be done using the Deployment APIs. These APIs allow you to specify the model you wish to use.

#### In-context learning
The models used by the Azure OpenAI Service use natural language instructions and examples provided during the generation call to identify the task being asked and skill required. When you use this approach, the first part of the prompt includes natural language instructions and/or examples of the specific task desired. The model then completes the task by predicting the most probable next piece of text. This technique is known as "in-context" learning. These models aren't retrained during this step but instead give predictions based on the context you include in the prompt.

There are three main approaches for in-context learning: Few-shot, one-shot and zero-shot. These approaches vary based on the amount of task-specific data that is given to the model:

**Few-shot**: In this case, a user includes several examples in the call prompt that demonstrate the expected answer format and content. The following example shows a few-shot prompt where we provide multiple examples:

    Convert the questions to a command:
    Q: Ask Constance if we need some bread
    A: send-msg `find constance` Do we need some bread?
    Q: Send a message to Greg to figure out if things are ready for Wednesday.
    A: send-msg `find greg` Is everything ready for Wednesday?
    Q: Ask Ilya if we're still having our meeting this evening
    A: send-msg `find ilya` Are we still having a meeting this evening?
    Q: Contact the ski store and figure out if I can get my skis fixed before I leave on Thursday
    A: send-msg `find ski store` Would it be possible to get my skis fixed before I leave on Thursday?
    Q: Thank Nicolas for lunch
    A: send-msg `find nicolas` Thank you for lunch!
    Q: Tell Constance that I won't be home before 19:30 tonight — unmovable meeting.
    A: send-msg `find constance` I won't be home before 19:30 tonight. I have a meeting I can't move.
    Q: Tell John that I need to book an appointment at 10:30
    A: 
The number of examples typically range from 0 to 100 depending on how many can fit in the maximum input length for a single prompt. Maximum input length can vary depending on the specific models you use. Few-shot learning enables a major reduction in the amount of task-specific data required for accurate predictions. This approach will typically perform less accurately than a fine-tuned model.

**One-shot**: This case is the same as the few-shot approach except only one example is provided.

**Zero-shot**: In this case, no examples are provided to the model and only the task request is provided.

#### Models
The service provides users access to several different models. Each model provides a different capability and price point.

GPT-4 models are the latest available models. These models are currently in preview. For access, existing Azure OpenAI Service customers can apply by filling out this [form](https://customervoice.microsoft.com/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR7en2Ais5pxKtso_Pz4b1_xURjE4QlhVUERGQ1NXOTlNT0w1NldTWjJCMSQlQCN0PWcu).

The GPT-3 base models are known as Davinci, Curie, Babbage, and Ada in decreasing order of capability and increasing order of speed.

The Codex series of models is a descendant of GPT-3 and has been trained on both natural language and code to power natural language to code use cases. Learn more about each model on our [models concept page](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models).

The following table describes model families currently available in Azure OpenAI Service. Not all models are available in all regions currently. Please refer to the capability table at the bottom for a full breakdown.

| Model family	| Description |
|---|---|
|[GPT-4](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#gpt-4-models)|A set of models that improve on GPT-3.5 and can understand as well as generate natural language and code. These models are currently in preview.|
|[GPT-3](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#gpt-3-models)|A series of models that can understand and generate natural language. This includes the new [ChatGPT model (preview)](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/chatgpt?pivots=programming-language-chat-completions).|
|[Codex](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#codex-models)|A series of models that can understand and generate code, including translating natural language to code.|
|[Embeddings](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#embeddings-models)|A set of models that can understand and use embeddings. An embedding is a special format of data representation that can be easily utilized by machine learning models and algorithms. The embedding is an information dense representation of the semantic meaning of a piece of text. Currently, we offer three families of Embeddings models for different functionalities: similarity, text search, and code search.|

To learn more visit [Azure OpenAI Service models](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models).

#### Responsible AI with the Azure OpenAI Service
At Microsoft, we're committed to the advancement of AI driven by principles that put people first. Generative models such as the ones available in Azure OpenAI Service have significant potential benefits, but without careful design and thoughtful mitigations, such models have the potential to generate incorrect or even harmful content. Microsoft has made significant investments to help guard against abuse and unintended harm, which includes requiring applicants to show well-defined use cases, incorporating Microsoft’s [principles for responsible AI use](https://www.microsoft.com/ai/responsible-ai?activetab=pivot1:primaryr6), building content filters to support customers, and providing responsible AI implementation guidance to onboarded customers.

More details on the RAI guidelines for the Azure OpenAI Service can be found [here](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/transparency-note?context=/azure/cognitive-services/openai/context/context).


## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
