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