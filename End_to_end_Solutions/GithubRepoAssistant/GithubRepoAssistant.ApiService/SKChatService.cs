using Azure;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Memory;
using System.Text;

namespace GithubRepoAssistant.ApiService;

public class SKChatService
{
    private readonly IKernel _kernel;
    private readonly ISemanticTextMemory _semanticTextMemory;
    private readonly string _collectionName;
    private readonly string _embeddingDeployment;
    private readonly OpenAIClient _openAiClient;
    private readonly Qdrant.Client.QdrantClient _qdrantClient;
    private bool _chatWasReset;


    public ChatHistory History { get; }

    public SKChatService(ISemanticTextMemory semanticTextMemory, IConfiguration configuration, Qdrant.Client.QdrantClient qdrantClient)
    {
        _chatWasReset = false;
        if (!configuration.TryReadFromConfig(out AIOptions? aiOptions))
        {
            throw new ArgumentNullException(nameof(aiOptions));
        }

        string openAiApiKey = aiOptions.ApiKey;
        string openAiEndpoint = aiOptions.Endpoint;
        _embeddingDeployment = aiOptions.EmbeddingDeployment;
        _qdrantClient = qdrantClient;

        _openAiClient = new(new System.Uri(openAiEndpoint), new AzureKeyCredential(openAiApiKey));
        var kernel = new KernelBuilder()
            .WithAzureChatCompletionService(aiOptions.ChatDeployment, openAiEndpoint, openAiApiKey)
            .Build();

        _kernel = kernel;
        _semanticTextMemory = semanticTextMemory;
        _collectionName = "gh_issues";
        History = _kernel.GetService<IChatCompletion>().CreateNewChat("""
            You are a helpful AI agent that has access to information about GitHub Issues in a specific repository.
            You are an expert in all the APIs of .NET libraries, the CLR runtime and the SDK, and the .NET ecosystem.
            You are an expert in the .NET runtime and the .NET SDK.
            You are an expert in triaging issues and labeling them.
            You are an expert in finding issues that are related to a specific theme, namespace, or package in .NET
            This repository you are about to triage is called dotnet/runtime.
            You have access to issues in this repository.
            Each issue has a title, a description, an area label, and a URL.
            Use only those retrieved information from those documents to answer user questions.
            """);

        History.AddAssistantMessage($"""
                Hi! I'm the dotnet/runtime assistant. I can help with finding issues matching a theme.
                What issues are you interested to find in this repository?
                """);
    }

    public void ResetSystemRule(string newSystemRule)
    {
        _chatWasReset = true;
        History.RemoveAll(m => true);
        History.AddSystemMessage(newSystemRule);
    }

    public async Task<string> AskQuestionAsync(string userQuestion)
    {
        if (_chatWasReset)
        {
            History.AddUserMessage(userQuestion);
            var msg = await _kernel.GetService<IChatCompletion>().GenerateMessageAsync(History);
            History.AddAssistantMessage(msg);
            return msg;
        }

        var searchResults = _semanticTextMemory.SearchAsync(_collectionName, userQuestion, 3, 0.5);

        var message = new StringBuilder();
        message.AppendLine("Given the following issues:");

        await foreach (var item in searchResults)
        {
            message.AppendLine("<issue>");
            message.AppendLine(item?.Metadata?.Text);
            float[]? floats = item?.Embedding?.ToArray();
            double? scoreZeroToOne = item?.Relevance;
            Type? type = item?.GetType();
            string? stringRepresentation = item?.ToString();
            message.AppendLine("</issue>");
        }

        message.AppendLine($"""
                    Answer only using the issues provided.
                    Make sure to report only unique issues and don't make up fake URLs.
                    For each issue, provide the title, the URL, and a one-sentence compact summary of the issue.
                    If there are multiple issues, then provide the top 3 issues.
                    If there are no issues, then say "I found no issues related to the question."
                    If you can suggest more labels to categorize the issues, then please do so.
                        - For example, 
                            - if the issue is a bug or a feature request, then you could say "This issue is a bug" or "This issue is a feature request."
                            - if the issue is about a specific area, then you could say "This issue is about the X area."
                            - if the issue is discussing a specific API, then you could say "This issue is about the Z API."
                            - if the issue is about a specific package, then you could say "This issue is about the Q package."
                    You could recommend for each issue what is the best response.
                    Do no hesitate to respond back to me with a technical response recommendation.
                    Let me know if any of the issues can be closed.
                        - If yes, then give me three proposed responses next to closing them, so I could pick out of your recommendations.
                            - for example, you could say (but not limited to the following):
                                - "Thank you for reporting this issue. We have fixed it in the latest version of the product. Please let us know if you are still experiencing this issue."
                                - "Thank you for your feedback. This is not a bug. Please use the following link to submit a feature request."
                        - If no, then give me three proposed responses next to keeping them open, so I could pick out of your recommendations.
                    """);

        message.AppendLine($"""
                Use the following format:
                
                These are the issues and the common themes are AOT and Reflection. 
                
                1. Title: ConfigurationBinder emits AOT warnings even when using Source Generator when passing result into a method Issue 
                  - URL: https://github.com/dotnet/runtime/issues/94544 
                  - Summary: The issue is reporting on the emitted AOT/trim warnings while using the Source Generator for ConfigurationBinder .Get<T>().
                  - I've read through this issue and have the following recommendations with respect to triaging it:
                      - This issue is a bug.
                      - This issue is about the System.Text.Json namespace.
                      - This might be a complicated issue to fix.
                      - I recommend to keep this issue open. (or say I recommend to close this issue).
                      - I recommend to close this issue with the following response: 
                        "Thank you for reporting this issue. 
                         We have fixed it in the latest version of the product.
                         Please let us know if you are still experiencing this issue."
                      - My technical recommendation is to fix the issue by doing the following:
                        "The issue is caused by the following code in the ConfigurationBinder class:
                         ...
                         The fix is to change the code to the following:
                         ...
                         "
                
                2. 
                """);

        message.AppendLine($"Question: {userQuestion}");
        message.AppendLine($"Answer: ");
        History.AddUserMessage(message.ToString());

        var chatService = _kernel.GetService<IChatCompletion>();
        var reply = await chatService.GenerateMessageAsync(History);

        History.AddAssistantMessage(reply);

        return reply;
    }

    public async Task<string[]> SearchQueryAsync(string query)
    {
        var collections = await _qdrantClient.ListCollectionsAsync();

        if (collections == null || !collections.Any())
        {
            // TODO log error
            return [];
        }

        var embeddingResponse = await _openAiClient.GetEmbeddingsAsync(_embeddingDeployment, new EmbeddingsOptions(new[] { query }));
        var embeddingVector = embeddingResponse.Value.Data[0].Embedding.ToArray();

        var results = await _qdrantClient.SearchAsync(_collectionName, embeddingVector, limit: (ulong)2);
        return results.Select(r => r.Payload["text"].StringValue).ToArray();
    }
}