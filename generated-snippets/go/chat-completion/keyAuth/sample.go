package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/openai/openai-go/v2"
	"github.com/openai/openai-go/v2/option"
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

	resp, err := client.Chat.Completions.New(context.TODO(), openai.ChatCompletionNewParams{
		Model: openai.ChatModel(deploymentName),
		Messages: []openai.ChatCompletionMessageParamUnion{
			{
				OfSystem: &openai.ChatCompletionSystemMessageParam{
					Content: openai.ChatCompletionSystemMessageParamContentUnion{
						OfString: openai.String("You are a helpful assistant. You will talk like a pirate."),
					},
				},
			},
			{
				OfUser: &openai.ChatCompletionUserMessageParam{
					Content: openai.ChatCompletionUserMessageParamContentUnion{
						OfString: openai.String("What's the best way to train a parrot?"),
					},
				},
			},
		},
	})

	if err != nil {
		log.Printf("ERROR: %s", err)
		return
	}

	for _, choice := range resp.Choices {
		if choice.Message.Content != "" {
			fmt.Fprintf(os.Stderr, "Content[%d]: %s\n", choice.Index, choice.Message.Content)
		}
	}
}