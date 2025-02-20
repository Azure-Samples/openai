param (
    [string]$envFilePath = ".env"
)
function Add-EnvVariables {
    param (
        [string]$envFilePath = ".env"
    )

    # Check if the .env file exists
    if (Test-Path $envFilePath) {
        $envContent = Get-Content $envFilePath

        foreach ($line in $envContent) {
            # Ignore comments and empty lines
            if (-not ($line -match '^\s*#') -and $line -match '\S') {
                # Split each line into key and value
                $key, $value = $line -split '=', 2

                # Set the environment variable
                [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
            }
        }

        Write-Host "Environment variables loaded from $envFilePath"
    } else {
        Write-Host ".env file not found."
    }
}


Add-EnvVariables -envFilePath $envFilePath
