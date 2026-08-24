using Azure.Identity; 
using OpenAI;
using OpenAI.Responses;
using System.ClientModel.Primitives;

#pragma warning disable OPENAI001

var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? throw new InvalidOperationException("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is not set.");
var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT environment variable is not set.");

BearerTokenPolicy tokenPolicy = new(
    new DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default");

OpenAIResponseClient client = new(
    model: deploymentName,
    authenticationPolicy: tokenPolicy,
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
