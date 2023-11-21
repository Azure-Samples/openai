using System.Diagnostics.CodeAnalysis;

namespace WebApplication2;

public record ChatConfig(string ApiKey, string ChatModel, string CollectionName)
{
    public static bool TryReadFromConfig(IConfiguration configuration, [NotNullWhen(true)] out ChatConfig? result)
    {
        var apiKey = configuration["AI:OpenAI:APIKey"];
        var chatModel = configuration["AI:OpenAI:ChatName"] ?? "gpt-3.5-turbo-16k";
        var collectionName = configuration["AI:OpenAI:CollectionName"];
        result = !string.IsNullOrWhiteSpace(apiKey) && !string.IsNullOrWhiteSpace(collectionName) ? new ChatConfig(apiKey, chatModel, collectionName) : null;
        return result is not null;
    }
}
