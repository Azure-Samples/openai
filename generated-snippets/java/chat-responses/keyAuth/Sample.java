import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.models.ChatModel;
import com.openai.models.responses.ResponseCreateParams;

import com.openai.azure.credential.AzureApiKeyCredential; 

public class Sample {
    public static void main(String[] args) {

    String endpoint = System.getenv("AZURE_OPENAI_ENDPOINT");
    if (endpoint == null || endpoint.isEmpty()) {
        System.out.println("Please set the AZURE_OPENAI_ENDPOINT environment variable.");
        System.exit(1);
    }
    String apiKey = System.getenv("AZURE_OPENAI_API_KEY");
    if (apiKey == null || apiKey.isEmpty()) {
        System.out.println("Please set the AZURE_OPENAI_API_KEY environment variable.");
        System.exit(1);
    }
    String deploymentName = System.getenv("AZURE_OPENAI_DEPLOYMENT");
    if (deploymentName == null || deploymentName.isEmpty()) {
        System.out.println("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.");
        System.exit(1);
    }

        OpenAIClient client = OpenAIOkHttpClient.builder()
                .baseUrl(endpoint)
                .credential(AzureApiKeyCredential.create(apiKey))
                .build();

        ResponseCreateParams.Builder paramsBuilder = ResponseCreateParams.builder()
                .model(deploymentName)
                .input("What's the capital of France?");


        ResponseCreateParams createParams = paramsBuilder.build();

        client.responses().create(createParams).output().stream()
                .flatMap(item -> item.message().stream())
                .flatMap(message -> message.content().stream())
                .flatMap(content -> content.outputText().stream())
                .forEach(outputText -> System.out.println(outputText.text()));
    }
}