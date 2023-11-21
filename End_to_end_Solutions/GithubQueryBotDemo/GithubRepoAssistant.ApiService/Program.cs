using GithubRepoAssistant.ApiService;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Qdrant.Client;

var builder = WebApplication.CreateBuilder(args);

builder.AddServiceDefaults();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Issue Labeler Search", Version = "v1", Description = "Search through dotnet/runtime issues." });
});

builder.Services.AddSingleton<SKChatService>();
builder.Services.AddSingleton<QdrantClient>(sp =>
{
    return new QdrantClient(host: "localhost", port: 6334, https: false);
});

builder.Services.AddSingleton<ISemanticTextMemory>(sp =>
{
    var configuration = sp.GetRequiredService<IConfiguration>();
    if (!configuration.TryReadFromConfig(out AIOptions? aiOptions))
    {
        throw new ArgumentNullException(nameof(aiOptions));
    }

    if (!configuration.TryReadFromConfig(out MemoryOptions? memoryOptions))
    {
        throw new ArgumentNullException(nameof(memoryOptions));
    }

    var memoryBuilder = new MemoryBuilder();
    var textEmbedding = new AzureTextEmbeddingGeneration(aiOptions.EmbeddingDeployment, aiOptions.Endpoint, aiOptions.ApiKey);
    memoryBuilder.WithTextEmbeddingGeneration(textEmbedding);
    memoryBuilder.WithQdrantMemoryStore(memoryOptions.QdrantEndpoint, 1536);

    return memoryBuilder.Build();
});

builder.Services.AddSingleton<IChatCompletion>(sp =>
        sp.GetRequiredService<IKernel>().GetService<IChatCompletion>());

var app = builder.Build();

app.MapDefaultEndpoints();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Use SKChatService to handle user questions
app.MapPost("/chat", async (SKChatService s, [FromBody] string q) => await s.AskQuestionAsync(q));

// Use SKChatService to handle user questions
app.MapPost("/search", async (SKChatService s, [FromBody] string q) => await s.SearchQueryAsync(q));

// Use SKChatService to reset the conversation state
app.MapGet("/reset", (SKChatService s) => s.History.RemoveAll(m => m.Role != AuthorRole.System));

// Use SKChatService to reset the system rule and conversation state
app.MapPost("/hardreset", (SKChatService s, [FromBody] string q) => s.ResetSystemRule(q));

// Use SKChatService to reset the conversation state
app.MapGet("/rules", (SKChatService s) =>
{
    var systemRules = s.History.Where(m => m.Role == AuthorRole.System);
    var rules = Enumerable.Range(1, systemRules.Count()).Select(index =>
        new Rule
        (
            index,
            systemRules.ElementAt(index - 1).Content.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)
        ))
        .ToArray();

    return rules;
});

app.Run();

record Rule(int Number, string[] lines);