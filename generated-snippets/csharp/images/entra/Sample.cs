using Azure.Identity; 
using OpenAI;
using OpenAI.Images;
using System;
using System.IO;
using System.ClientModel.Primitives;

#pragma warning disable OPENAI001

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT environment variable is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? throw new InvalidOperationException("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is not set.");
BearerTokenPolicy tokenPolicy = new(
    new DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default");

ImageClient client = new(
    authenticationPolicy: tokenPolicy,
    model: deploymentName,
    options: new OpenAIClientOptions()
    {
        Endpoint = new($"{endpoint}"),
    });

string prompt = "A cute baby polar bear";

ImageGenerationOptions options = new()
{   
    Size = GeneratedImageSize.W1024xH1024,
};

GeneratedImage image = client.GenerateImage(prompt, options);
BinaryData bytes = image.ImageBytes;

using FileStream stream = File.OpenWrite("output.png");
bytes.ToStream().CopyTo(stream);