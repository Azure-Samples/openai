#nullable disable
namespace WebApplication2;

public class AIOptions
{
    public string OpenAIApiKey { get; set; }
    public string OpenAIEndpoint { get; set; }
    public string OpenAIChatDeployment { get; set; }
    public string OpenAIEmbeddingDeployment { get; set; }
    public string QdrantEndpoint { get; set; }
    public string CollectionName { get; set; }
}
