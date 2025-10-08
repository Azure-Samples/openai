package main

import (
	"context"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/option"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	endpoint := os.Getenv("AZURE_OPENAI_ENDPOINT")
	if len(endpoint) == 0 {
		fmt.Println("Please set the AZURE_OPENAI_ENDPOINT environment variable.")
		os.Exit(1)
	}
	apiKey := os.Getenv("AZURE_OPENAI_API_KEY")
	if len(apiKey) == 0 {
		fmt.Println("Please set the AZURE_OPENAI_API_KEY environment variable.")
		os.Exit(1)
	}
	deploymentName := os.Getenv("AZURE_OPENAI_DEPLOYMENT")
	if len(deploymentName) == 0 {
		fmt.Println("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.")
		os.Exit(1)
	}

		client := openai.NewClient(
		option.WithBaseURL(endpoint),
		option.WithAPIKey(apiKey),
		)
	ctx := context.Background()

	question := "Write me a haiku about computers"

	resp, err := client.Responses.New(ctx, responses.ResponseNewParams{
		Input: responses.ResponseNewParamsInputUnion{OfString: openai.String(question)},
		Model: deploymentName,
	})

	if err != nil {
		panic(err)
	}

	println(resp.OutputText())
}
