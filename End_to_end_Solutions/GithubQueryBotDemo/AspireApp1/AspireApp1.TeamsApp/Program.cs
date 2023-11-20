using AspireApp1.TeamsApp;
using AspireTeamsApp;
using AspireTeamsApp.Bot;
using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Integration.AspNet.Core;
using Microsoft.Bot.Connector.Authentication;

var builder = WebApplication.CreateBuilder(args);

builder.AddServiceDefaults();

builder.Services.AddControllers();
builder.Services.AddHttpClient("WebClient", client => client.Timeout = TimeSpan.FromSeconds(600));
builder.Services.AddHttpContextAccessor();

// Create the Bot Framework Authentication to be used with the Bot Adapter.
var config = builder.Configuration.Get<ConfigOptions>();
builder.Configuration["MicrosoftAppType"] = "MultiTenant";
builder.Configuration["MicrosoftAppId"] = config.BOT_ID;
builder.Configuration["MicrosoftAppPassword"] = config.BOT_PASSWORD;
builder.Services.AddSingleton<BotFrameworkAuthentication, ConfigurationBotFrameworkAuthentication>();

// Create the Cloud Adapter Bot Framework Adapter with error handling enabled.
//builder.Services.AddSingleton<CloudAdapter, AdapterWithErrorHandler>();
builder.Services.AddSingleton<IBotFrameworkHttpAdapter, AdapterWithErrorHandler>();

// Create the bot as a transient. In this case the ASP Controller is expecting an IBot.
//builder.Services.AddTransient<IBot, TeamsEchoBot>();
builder.Services.AddTransient<IBot>(sp =>
{
    // to set this up, I would have preferred to use
    // AddHttpClient<ApiServiceClient>
    // combined with AddTransient<IBot, TeamsEchoBot>()
    // but because dev tunnels with .NET aspire is not yet supported
    // and this other endpoint is using qdrant
    // then it needs more thought
    var httpClient = new HttpClient()
    {
        BaseAddress = new("http://localhost:5084")
    };

    var apiService = new ApiServiceClient(httpClient);
    //var apiService = sp.GetService<ApiServiceClient>();

    return new TeamsEchoBot(apiService);
});

//builder.Services.AddHttpClient<ApiServiceClient>(client => client.BaseAddress = new("http://apiservice"));

var app = builder.Build();

app.MapDefaultEndpoints();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
app.UseStaticFiles();

app.UseRouting();

app.UseAuthentication();
app.UseAuthorization();

app.UseEndpoints(endpoints =>
{
    endpoints.MapControllers();
});

app.Run();