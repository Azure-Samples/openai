
var builder = DistributedApplication.CreateBuilder(args);

var apiservice = builder.AddProject<Projects.GithubRepoAssistant_ApiService>("apiservice");

builder.AddProject<Projects.Web>("webfrontend")
    .WithReference(apiservice);

builder.AddProject<Projects.TeamsApp>("teamsapp")
    .WithReference(apiservice);

builder.Build().Run();
