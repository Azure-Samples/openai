using OpenAI;
using OpenAI.Responses;
using System.ClientModel;

#pragma warning disable OPENAI001

var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? throw new InvalidOperationException("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is not set.");
var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT environment variable is not set.");
var apiKey = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY") ?? throw new InvalidOperationException("AZURE_OPENAI_API_KEY environment variable is not set.");

OpenAIResponseClient client = new(
    model: deploymentName,
    credential: new ApiKeyCredential(apiKey),
    options: new OpenAIClientOptions()
    {
        Endpoint = new($"{endpoint}"),
    });

ResponseCreationOptions options = new ResponseCreationOptions{
    Temperature=(float)0.7,
};

OpenAIResponse response = client.CreateResponse(
     [
        ResponseItem.CreateUserMessageItem("What's the weather like today for my current location?"),
     ], options);

Console.WriteLine($"[ASSISTANT]: {response.GetOutputText()}");
