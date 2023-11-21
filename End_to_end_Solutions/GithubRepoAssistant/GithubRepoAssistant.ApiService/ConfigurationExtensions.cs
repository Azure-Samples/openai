using System.Diagnostics.CodeAnalysis;

namespace GithubRepoAssistant.ApiService;

public static class ConfigurationExtensions
{
    public static bool TryReadFromConfig(this IConfiguration configuration, [NotNullWhen(true)] out AIOptions? result)
    {
        var apiKey = configuration["AIOptions:ApiKey"];
        var endpoint = configuration["AIOptions:Endpoint"];
        var chatModel = configuration["AIOptions:ChatDeployment"];
        var embeddingName = configuration["AIOptions:EmbeddingDeployment"];
        result =
            !string.IsNullOrWhiteSpace(apiKey) &&
            !string.IsNullOrWhiteSpace(endpoint) &&
            !string.IsNullOrWhiteSpace(chatModel) &&
            !string.IsNullOrWhiteSpace(embeddingName)
            ? new AIOptions(apiKey, endpoint, chatModel, embeddingName) : null;
        return result is not null;
    }

    public static bool TryReadFromConfig(this IConfiguration configuration, [NotNullWhen(true)] out MemoryOptions? result)
    {
        var endpoint = configuration["QdrantOptions:QdrantEndpoint"];
        var collectionName = configuration["QdrantOptions:CollectionName"];
        result =
            !string.IsNullOrWhiteSpace(endpoint) &&
            !string.IsNullOrWhiteSpace(collectionName)
            ? new MemoryOptions(endpoint, collectionName) : null;
        return result is not null;
    }
}

