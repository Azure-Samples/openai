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

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
    temperature=0.7,
)

print(completion.choices[0].message)