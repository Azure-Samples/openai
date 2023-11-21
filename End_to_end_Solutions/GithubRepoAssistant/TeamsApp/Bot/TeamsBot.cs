using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Teams;
using Microsoft.Bot.Schema;

namespace TeamsApp.Bot;

public class TeamsBot : TeamsActivityHandler
{
    private readonly ApiServiceClient _apiServiceClient;
    public TeamsBot(ApiServiceClient weatherApiClient)
    {
        _apiServiceClient = weatherApiClient;
    }

    protected override async Task OnMessageActivityAsync(ITurnContext<IMessageActivity> turnContext, CancellationToken cancellationToken)
    {
        string messageText = turnContext.Activity.RemoveRecipientMention()?.Trim();
        if (string.IsNullOrEmpty(messageText))
        {
            await turnContext.SendActivityAsync("Please ask again. The message seems to be empty.");
            return;
        }

        // Listen for user to say '/reset' and then delete conversation state
        if (messageText.Equals("/reset", StringComparison.OrdinalIgnoreCase))
        {
            await _apiServiceClient.ResetChatAsync();
            await turnContext.SendActivityAsync("Ok I've deleted the current conversation state");
        }
        // Listen for user to say '/rules' and then show system rule for chat service
        else if (messageText.Equals("/rules", StringComparison.OrdinalIgnoreCase))
        {
            var rules = await _apiServiceClient.GetRulesAsync();
            await turnContext.SendActivityAsync(MessageFactory.Text($$"""
            Rules:
            {{ string.Join(Environment.NewLine, rules.SelectMany(x => x.Lines))}}
            """));
        }
        else
        {
            var chatResponse = await _apiServiceClient.PostChatAsJsonAsync(messageText);
            if (chatResponse is null)
            {
                await turnContext.SendActivityAsync(FailureMessage());
            }
            else
            {
                await turnContext.SendActivityAsync(chatResponse);
            }
        }

        static string FailureMessage() => $"Chat endpoint was not responsive for the Teams chatbot.";
    }

    protected override async Task OnMembersAddedAsync(IList<ChannelAccount> membersAdded, ITurnContext<IConversationUpdateActivity> turnContext, CancellationToken cancellationToken)
    {
        var welcomeText = "Hi there! I'm a Teams bot.";
        foreach (var member in membersAdded)
        {
            if (member.Id != turnContext.Activity.Recipient.Id)
            {
                await turnContext.SendActivityAsync(MessageFactory.Text(welcomeText), cancellationToken);
            }
        }
    }
}

