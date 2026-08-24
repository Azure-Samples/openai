import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.models.ChatModel;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import com.openai.models.chat.completions.ChatCompletionMessage;

import com.azure.identity.AuthenticationUtil;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.openai.credential.BearerTokenCredential; 

public class Sample {
    public static void main(String[] args) {

    String endpoint = System.getenv("AZURE_OPENAI_ENDPOINT");
    if (endpoint == null || endpoint.isEmpty()) {
        System.out.println("Please set the AZURE_OPENAI_ENDPOINT environment variable.");
        System.exit(1);
    }
    String deploymentName = System.getenv("AZURE_OPENAI_DEPLOYMENT");
    if (deploymentName == null || deploymentName.isEmpty()) {
        System.out.println("Please set the AZURE_OPENAI_DEPLOYMENT environment variable.");
        System.exit(1);
    }

         OpenAIClient client = OpenAIOkHttpClient.builder()
                .baseUrl(endpoint)
                // Set the Azure Entra ID
                .credential(BearerTokenCredential.create(AuthenticationUtil.getBearerTokenSupplier(
                        new DefaultAzureCredentialBuilder().build(), "https://cognitiveservices.azure.com/.default")))
                .build();

        ChatCompletionCreateParams createParams = ChatCompletionCreateParams.builder()
                .model(ChatModel.of(deploymentName))
                .addSystemMessage("You are a helpful assistant. You will talk like a pirate.")
                .addUserMessage("Can you help me?")
                .addUserMessage("What's the best way to train a parrot?")
                .build();

        ChatCompletion chatCompletion = client.chat().completions().create(createParams);
        System.out.printf("Model ID=%s is created at %s.%n", chatCompletion.id(), chatCompletion.created());

        for (ChatCompletion.Choice choice : chatCompletion.choices()) {
            ChatCompletionMessage message = choice.message();
            System.out.println("Message:");
            System.out.println(message.content());
        }
    }
}