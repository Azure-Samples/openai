
var builder = DistributedApplication.CreateBuilder(args);

var apiservice = builder.AddProject<Projects.AspireApp1_ApiService>("apiservice");

builder.AddProject<Projects.AspireApp1_Web>("webfrontend")
    .WithReference(apiservice);

builder.AddProject<Projects.AspireApp1_TeamsApp>("myteamsapp")
    .WithReference(apiservice);

builder.Build().Run();
