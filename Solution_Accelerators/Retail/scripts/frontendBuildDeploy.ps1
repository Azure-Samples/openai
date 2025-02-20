# scripts/frontendBuildDeploy.ps1 -resourceGroup <RESOURCE-GROUP> -webAppName <WEB-APP-NAME> -frontendPath <FRONTEND-PATH>

param (
    [Parameter(Mandatory=$true)][string]$resourceGroup,
    [Parameter(Mandatory=$true)][string]$webAppName,
    [Parameter(Mandatory=$true)][string]$frontendPath
)

function Invoke-Command {
    param (
        [Parameter(Mandatory = $true)]
        [ScriptBlock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    & $Command

    if ($LASTEXITCODE -ne 0) {
        Write-Error $ErrorMessage
        exit $LASTEXITCODE
    }
}

$projectRoot = Get-Location
Write-Host "Project root is: $projectRoot"

$frontendRoot = Join-Path $projectRoot $frontendPath

$artifactStagingDirectory = Join-Path $projectRoot "artifact"
if (-Not (Test-Path $artifactStagingDirectory)) {
    Write-Host "Creating artifact staging directory at $artifactStagingDirectory..."
    New-Item -ItemType Directory -Path $artifactStagingDirectory | Out-Null
}

$buildId = (Get-Date -Format "yyyyMMddHHmmss")
$zipFilePath = Join-Path $artifactStagingDirectory "$buildId.zip"

Invoke-Command -Command { 
    $global:nodeVersion = node --version 
    Write-Host "Node.js version: $global:nodeVersion" 
} -ErrorMessage "Node.js is not installed or not available in your PATH. Please install Node.js 18.x."

Write-Host "Running 'npm install' in $frontendRoot..."
Push-Location $frontendRoot
Invoke-Command -Command { npm install } -ErrorMessage "'npm install' failed."

Write-Host "Running 'npm run build'..."
Invoke-Command -Command { npm run build } -ErrorMessage "'npm run build' failed."
Pop-Location

Write-Host "Archiving files from $frontendRoot to $zipFilePath..."
if (Test-Path $zipFilePath) {
    Remove-Item $zipFilePath -Force
}
Invoke-Command -Command { Compress-Archive -Path (Join-Path $frontendRoot "*") -DestinationPath $zipFilePath } -ErrorMessage "Failed to create archive."

Write-Host "Setting startup command to 'npm start' for Azure Web App '$webAppName'..."
Invoke-Command -Command { az webapp config set --resource-group $resourceGroup --name $webAppName --startup-file "npm start" } -ErrorMessage "Failed to set startup command for the web app."

Write-Host "Deploying to Azure Web App '$webAppName'..."
Invoke-Command -Command { az webapp deployment source config-zip --resource-group $resourceGroup --name $webAppName --src $zipFilePath } -ErrorMessage "Azure deployment failed."

Write-Host "Deployment completed successfully."

Invoke-Command -Command { az webapp list --resource-group $resourceGroup --query "[?state=='Running']" } -ErrorMessage "Failed to list web apps."