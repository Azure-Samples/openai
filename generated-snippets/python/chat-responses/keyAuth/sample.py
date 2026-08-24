import os
from openai import OpenAI

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
if not endpoint:
  raise ValueError("Please set the AZURE_OPENAI_ENDPOINT environment variable.")

deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
if not deployment_name:
  raise ValueError("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.")

api_key = os.environ.get("AZURE_OPENAI_API_KEY")
if not api_key:
  raise ValueError("Please set the AZURE_OPENAI_API_KEY environment variable.")


client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

response = client.responses.create(
    model=deployment_name,
    input="What is the capital of France?",
)

print(f"answer: {response.output[0]}")
