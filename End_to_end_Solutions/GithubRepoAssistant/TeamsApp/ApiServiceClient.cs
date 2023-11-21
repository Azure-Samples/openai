namespace TeamsApp;

public class ApiServiceClient(HttpClient httpClient)
{
    private readonly string remoteServiceBaseUrl = "/";

    public async Task<string> PostChatAsJsonAsync(string messageText)
    {
        var uri = $"{remoteServiceBaseUrl}chat";
        var reply = await httpClient.PostAsJsonAsync(uri, messageText);
        return await reply.Content.ReadAsStringAsync();
    }

    public async Task ResetChatAsync()
    {
        var uri = $"{remoteServiceBaseUrl}reset";
        await httpClient.GetAsync(uri);
    }
    public async Task<Rule[]> GetRulesAsync()
    {
        return await httpClient.GetFromJsonAsync<Rule[]>("/rules") ?? [];
    }
}
public record Rule(int Number, string[] Lines);
