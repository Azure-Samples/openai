import OpenAI from "openai";
import { getBearerTokenProvider, DefaultAzureCredential } from "@azure/identity";

const endpoint = process.env["AZURE_OPENAI_ENDPOINT"];
if (!endpoint) {
  console.error("Please set the AZURE_OPENAI_ENDPOINT environment variable.");
  process.exit(1);
}
const deploymentName = process.env["AZURE_OPENAI_DEPLOYMENT"];
if (!deploymentName) {
  console.error("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.");
  process.exit(1);
}
const tokenProvider = getBearerTokenProvider(
    new DefaultAzureCredential(),
    'https://cognitiveservices.azure.com/.default');

const openai = new OpenAI({
    baseURL: endpoint,
    apiKey: tokenProvider
});

async function main() {
  const completion = await openai.chat.completions.create({
    messages: [{ role: "developer", content: "You are a helpful assistant." }],
    model: deploymentName,
    store: true,
  });

  console.log(completion.choices[0]);
}

main();