import base64
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

img = client.images.generate(
    model=deployment_name,
    prompt="A cute baby polar bear",
    n=1,
    size="1024x1024",
)

image_bytes = base64.b64decode(img.data[0].b64_json)
with open("output.png", "wb") as f:
    f.write(image_bytes)
