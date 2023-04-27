# Speech to Speech chat
In this guide, you can use [Speech](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/overview) to converse with [Azure OpenAI](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/overview). The text recognized by the Speech service is sent to Azure OpenAI. The text response from Azure OpenAI is then synthesized by the Speech service.

Speak into the microphone to start a conversation with Azure OpenAI.

Azure Cognitive Services Speech recognizes your speech and converts it into text (speech-to-text).
Your request as text is sent to Azure OpenAI.
Azure Cognitive Services Speech synthesizes (text-to-speech) the response from Azure OpenAI to the default speaker.
Although the experience of this example is a back-and-forth exchange, Azure OpenAI doesn't remember the context of your conversation.
[Read more](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/openai-speech?tabs=linux).
