using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;

namespace Bot.Web.Pages
{
    public class IndexModel : PageModel
    {
        private readonly ILogger<IndexModel> _logger;
        private readonly IConfiguration _configuration;
        public IndexModel(ILogger<IndexModel> logger, IConfiguration config)
        {
            _logger = logger;
            _configuration = config;
        }

        public async Task OnGet()
        {
            //TODO: Get userId from user Auth to web site
            var userId = $"dl_{Guid.NewGuid()}";

            if (User.Identity.IsAuthenticated)
            {
                userId = User.Identity.Name?.ToString();
                foreach (var claim in User.Claims)
                {
                    if (claim.Type == "name")
                    {
                        var name = claim.Value;
                        var nameParts = name.Split(" ", StringSplitOptions.RemoveEmptyEntries);
                        var fName = nameParts[0];
                        ViewData["FirstName"] = fName;
                        userId = $"dl_{claim.Value.Replace(" ", "").ToLower()}";
                    }
                }
            }
            var client = new HttpClient();

            var webChatSecret = _configuration["WebchatSecret"];
            var speechApiKey = _configuration["SpeechSubscriptionKey"];
            var speechServiceRegion = _configuration["SpeechServiceRegion"];


            ViewData["WebChatUserId"] = userId;
            ViewData["WebChatToken"] = await GetDirectLineTokenAsync(client, webChatSecret, userId);
            ViewData["SpeechToken"] = await GetSpeechTokenAsync(client, speechApiKey, speechServiceRegion, userId);
            ViewData["SpeechRegion"] = speechServiceRegion;
        }

        private class DirectLineToken
        {
            public string conversationId { get; set; }
            public string token { get; set; }
            public int expires_in { get; set; }
        }

        private async Task<string> GetDirectLineTokenAsync(HttpClient client, string webChatSecret, string userId)
        {
            var request = new HttpRequestMessage(HttpMethod.Post, $"https://directline.botframework.com/v3/directline/tokens/generate");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", webChatSecret);

            request.Content = new StringContent(
            JsonConvert.SerializeObject(
                new { User = new { Id = userId } }),
                Encoding.UTF8,
                "application/json");

            var response = await client.SendAsync(request);
            var token = string.Empty;

            if (response.IsSuccessStatusCode)
            {
                var body = await response.Content.ReadAsStringAsync();
                token = JsonConvert.DeserializeObject<DirectLineToken>(body).token;
            }

            return token;
        }

        private async Task<string> GetSpeechTokenAsync(HttpClient client, string speechApiKey, string region, string userId)
        {
            var request = new HttpRequestMessage(HttpMethod.Post, $"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken");
            request.Headers.Add("Ocp-Apim-Subscription-Key", speechApiKey);

            request.Content = new StringContent(
            JsonConvert.SerializeObject(
                new { User = new { Id = userId } }),
                Encoding.UTF8,
                "application/json");

            var response = await client.SendAsync(request);
            var speechToken = string.Empty;

            if (response.IsSuccessStatusCode)
            {
                speechToken = await response.Content.ReadAsStringAsync();
            }

            return speechToken;
        }
    }
}
