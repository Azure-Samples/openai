import OpenAI from "openai";
import fs from "fs";

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

const prompt = "A cute baby polar bear.";

const result = await openai.images.generate({
    model: deploymentName,
    prompt,
});

// Save the image to a file
const image_base64 = result.data[0].b64_json;
const image_bytes = Buffer.from(image_base64, "base64");
fs.writeFileSync("output.png", image_bytes);