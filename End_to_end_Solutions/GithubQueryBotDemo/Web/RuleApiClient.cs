namespace AspireApp1.Web;

public class RuleApiClient(HttpClient httpClient)
{
    public async Task<Rule[]> GetRulesAsync()
    {
        return await httpClient.GetFromJsonAsync<Rule[]>("/rules") ?? [];
    }
}

public record Rule(int Number, string[] Lines);
