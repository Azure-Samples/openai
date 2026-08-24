import os
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
if not endpoint:
  raise ValueError("Please set the AZURE_OPENAI_ENDPOINT environment variable.")

deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
if not deployment_name:
  raise ValueError("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.")

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

client = OpenAI(
    base_url=endpoint,
    api_key=token_provider
)

response = client.responses.create(
    model=deployment_name,
    input="What is the capital of France?",
)

print(f"answer: {response.output[0]}")
