package main

import (
	"context"
	"encoding/base64"
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
	deploymentName := os.Getenv("AZURE_OPENAI_DEPLOYMENT")
	if len(deploymentName) == 0 {
		fmt.Println("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.")
		os.Exit(1)
	}
	apiKey := os.Getenv("AZURE_OPENAI_API_KEY")
	if len(apiKey) == 0 {
		fmt.Println("Please set the AZURE_OPENAI_API_KEY environment variable.")
		os.Exit(1)
	}

		client := openai.NewClient(
		option.WithBaseURL(endpoint),
		option.WithAPIKey(apiKey),
		)
	
	// Generate an image
	image, err := client.Images.Generate(context.Background(), openai.ImageGenerateParams{
		Prompt:         "A cute baby polar bear",
		Model:          deploymentName,
		N:              openai.Int(1),
	})
	if err != nil {
		panic(err)
	}

	// Save the image to a file
	imageBytes, err := base64.StdEncoding.DecodeString(image.Data[0].B64JSON)
	if err != nil {
		panic(err)
	}

	dest := "./output.png"
	println("Writing image to " + dest)
	err = os.WriteFile(dest, imageBytes, 0755)
	if err != nil {
		panic(err)
	}
}
