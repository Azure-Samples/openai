import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.models.images.ImageGenerateParams;
import com.openai.models.images.ImageModel;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;

import com.openai.azure.credential.AzureApiKeyCredential; 


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
    String apiKey = System.getenv("AZURE_OPENAI_API_KEY");
    if (apiKey == null || apiKey.isEmpty()) {
        System.out.println("Please set the AZURE_OPENAI_API_KEY environment variable.");
        System.exit(1);
    }

        OpenAIClient client = OpenAIOkHttpClient.builder()
                .baseUrl(endpoint)
                .credential(AzureApiKeyCredential.create(apiKey))
                .build();

        ImageGenerateParams imageGenerateParams = ImageGenerateParams.builder()
                .prompt("A cute baby polar bear")
                .model(deploymentName)
                .n(1)
                .build();

        client.images().generate(imageGenerateParams).data().orElseThrow().forEach(image -> {
                try {   
                        String base64String = image.b64Json().orElseThrow();
                        byte[] imageData = Base64.getDecoder().decode(base64String);
                        Files.write(Paths.get("output.png"), imageData);
                } catch (IOException e) {
                        e.printStackTrace();
                }
        });
    }
}