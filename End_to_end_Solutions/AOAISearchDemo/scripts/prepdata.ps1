# Set the Azure Key Vault details
$KeyVaultName = ""

Write-Host ""
Write-Host "Loading secrets from Azure Key Vault '$KeyVaultName' into env..."
Write-Host ""

# Install required Azure modules if not already installed
if (-not (Get-Module -Name Az.KeyVault -ListAvailable)) {
  Install-Module -Name Az.KeyVault -Force -AllowClobber
}

# Connect to Azure using your credentials
Connect-AzAccount

# Set the environment variables
$secrets = Get-AzKeyVaultSecret -VaultName $KeyVaultName -Name "*"
foreach ($secret in $secrets) {
  $name = $secret.Name
  $value = Get-AzKeyVaultSecret -VaultName $KeyVaultName -Name $name -AsPlainText
  $updatedName = $name.Replace("-", "_")
  [Environment]::SetEnvironmentVariable($updatedName, $value)
}

# Disconnect from Azure
Disconnect-AzAccount

Write-Host "Environment variables set."

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  # fallback to python3 if python not found
  $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

Write-Host 'Creating python virtual environment "scripts/.venv"'
Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m venv ./scripts/.venv" -Wait -NoNewWindow

$venvPythonPath = "./scripts/.venv/scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = "./scripts/.venv/bin/python"
}

Write-Host 'Installing dependencies from "requirements.txt" into virtual environment'
Start-Process -FilePath $venvPythonPath -ArgumentList "-m pip install -r ./scripts/requirements.txt" -Wait -NoNewWindow

Write-Host 'Packaging app directory'
Start-Process -FilePath $venvPythonPath -ArgumentList "-m pip install -e ./app" -Wait -NoNewWindow

Write-Host 'Running "prepdocs.py"'
$cwd = (Get-Location)
$predocsArguments = "./scripts/prepdocs.py", "$cwd/data/surface_device_documentation/",
  "--storageaccount", $env:AZURE_STORAGE_ACCOUNT,
  "--container", $env:AZURE_STORAGE_CONTAINER, 
  "--searchservice", $env:AZURE_SEARCH_SERVICE, 
  "--index", $env:AZURE_SEARCH_INDEX, 
  "--formrecognizerservice", $env:AZURE_FORMRECOGNIZER_SERVICE, "-v"
Start-Process -FilePath $venvPythonPath -ArgumentList $predocsArguments -Wait -NoNewWindow

Write-Host 'Running "prepopulate.py"'
$prepoulateArguments = "./scripts/prepopulate/prepopulate.py",
  "--entities_path", "./scripts/prepopulate/entries/entities.yaml",
  "--permissions_path", "./scripts/prepopulate/entries/permissions.yaml",
  "--cosmos_db_endpoint", $env:AZURE_COSMOS_ENDPOINT,
  "--cosmos_db_key", $env:AZURE_COSMOS_KEY,
  "--cosmos_db_name", $env:AZURE_COSMOS_DB_NAME,
  "--cosmos_db_entities_container_name", $env:AZURE_COSMOS_DB_ENTITIES_CONTAINER_NAME,
  "--cosmos_db_permissions_container_name", $env:AZURE_COSMOS_DB_PERMISSIONS_CONTAINER_NAME
Start-Process -FilePath $venvPythonPath -ArgumentList $prepoulateArguments -Wait -NoNewWindow

Write-Host 'Running "populate_sql.py"'
$populatesqlArguments = "./scripts/prepopulate/populate_sql.py",
  "--sql_connection_string", "`"$env:SQL_CONNECTION_STRING`""
Start-Process -FilePath $venvPythonPath -ArgumentList $populatesqlArguments -Wait -NoNewWindow