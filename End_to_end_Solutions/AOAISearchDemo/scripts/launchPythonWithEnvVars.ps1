#!/usr/bin/env pwsh
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, Position = 0)]
    [string]
    $pythonPath,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]
    $pythonScriptPath
)
Write-Host ""
Write-Host "Loading azd .env file from current environment"
Write-Host ""
foreach ($line in (& azd env get-values)) {
    if ($line -match "([^=]+)=(.*)") {
        $key = $matches[1]
        $value = $matches[2] -replace '^"|"$'
        Set-Item -Path "env:\$key" -Value $value
    }
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to load environment variables from azd environment"
    exit $LASTEXITCODE
}
Write-Host ""
Write-Host "Launching Python script with env vars loaded"
Write-Host ""
Start-Process -FilePath $pythonPath -ArgumentList $pythonScriptPath -Wait -NoNewWindow