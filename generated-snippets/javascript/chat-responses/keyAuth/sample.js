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
  const runner = openai.responses
    .stream({
      model: deploymentName,
      input: 'solve 8x + 31 = 2',
    })
    .on('event', (event) => console.log(event))
    .on('response.output_text.delta', (diff) => process.stdout.write(diff.delta));

  for await (const event of runner) {
    console.log('event', event);
  }

  const result = await runner.finalResponse();
  console.log(result);
}

main();
