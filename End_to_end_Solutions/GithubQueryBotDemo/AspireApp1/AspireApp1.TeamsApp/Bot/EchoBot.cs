using AspireApp1.TeamsApp;
using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Teams;
using Microsoft.Bot.Schema;

namespace AspireTeamsApp.Bot;

public class EchoBot : TeamsActivityHandler
{
    private readonly ApiServiceClient _apiServiceClient;
    public EchoBot(ApiServiceClient apiServiceClient)
    {
        _apiServiceClient = apiServiceClient;
    }

    protected override async Task OnMessageActivityAsync(ITurnContext<IMessageActivity> turnContext, CancellationToken cancellationToken)
    {
        string messageText = turnContext.Activity.RemoveRecipientMention()?.Trim();
        var replyText = $"Echo: {messageText}";
        if (messageText.Equals("/rules", StringComparison.OrdinalIgnoreCase))
        {
            var rules = await _apiServiceClient.GetRulesAsync();
            replyText = $"Echo: {messageText} - Rules:{Environment.NewLine}{string.Join(Environment.NewLine, rules.FirstOrDefault().Lines)}";
        }

        await turnContext.SendActivityAsync(MessageFactory.Text(replyText), cancellationToken);
    }
    protected override async Task OnMembersAddedAsync(IList<ChannelAccount> membersAdded, ITurnContext<IConversationUpdateActivity> turnContext, CancellationToken cancellationToken)
    {
        var welcomeText = "Hi there! I'm a Teams bot that will echo what you said to me.";
        foreach (var member in membersAdded)
        {
            if (member.Id != turnContext.Activity.Recipient.Id)
            {
                await turnContext.SendActivityAsync(MessageFactory.Text(welcomeText), cancellationToken);
            }
        }
    }
}

