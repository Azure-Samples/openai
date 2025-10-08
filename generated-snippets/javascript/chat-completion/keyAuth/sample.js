import OpenAI from "openai";

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
const apiKey = process.env["AZURE_OPENAI_API_KEY"];
if (!apiKey) {
  console.error("Please set the AZURE_OPENAI_API_KEY environment variable.");
  process.exit(1);
}

const openai = new OpenAI({
    baseURL: endpoint,
    apiKey: apiKey
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