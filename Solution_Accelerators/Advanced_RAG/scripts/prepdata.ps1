Write-Host ""
Write-Host "Setting variables ..."
Write-Host ""
$AZURE_STORAGE_ACCOUNT="storage_account_name"
$AZURE_STORAGE_CONTAINER="storage_container_name"
$AZURE_STORAGE_KEY="storage_key"
$AZURE_SEARCH_SERVICE="search_service_name"
$AZURE_SEARCH_KEY="search_service_key"
$AZURE_SEARCH_INDEX="search_index_name"
$AZURE_DOCUMENT_INTELLIGENCE_SERVICE="document_intelligence_service_name"
$AZURE_DOCUMENT_INTELLIGENCE_KEY="document_intelligence_key"
$SEARCH_SKIP_VECTORIZATION="true_or_false"
$AZURE_OPENAI_EMBEDDINGS_SERVICE="openai_embeddings_service_name"
$AZURE_OPENAI_EMBEDDINGS_API_KEY="openai_embeddings_api_key"
$AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME="preferred_openai_engine_for_embeddings"
$AZURE_OPENAI_EMBEDDINGS_TOKEN_LIMIT="token_limit_as_integer"
$AZURE_OPENAI_EMBEDDINGS_DIMENSIONS="embedding_dimensions_as_integer"
Write-Host ""
Write-Host "Variables set"
Write-Host ""

Write-Host ""
Write-Host "Installing dependencies..."
Write-Host ""
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  # fallback to python3 if python not found
  $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m venv ./scripts/.venv" -Wait -NoNewWindow

$venvPythonPath = "./scripts/.venv/Scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = "./scripts/.venv/bin/python"
}

$process = Start-Process -FilePath $venvPythonPath -ArgumentList "-m pip install -r ./indexing/requirements.txt" -Wait -NoNewWindow -PassThru

if ($process.ExitCode -ne 0) {
  Write-Host ""
  Write-Warning "Installing dependencies failed with non-zero exit code $LastExitCode."
  Write-Host ""
  exit $process.ExitCode
}


Write-Host ""
Write-Host 'Running "prepdocs.py"...'
Write-Host ""

$predocsArguments = "./indexing/prepdocs.py", "./data/",
  "--storageaccount", $AZURE_STORAGE_ACCOUNT,
  "--container", $AZURE_STORAGE_CONTAINER,
  "--storagekey", $AZURE_STORAGE_KEY,
  "--searchservice", $AZURE_SEARCH_SERVICE,
  "--searchkey", $AZURE_SEARCH_KEY, 
  "--index", $AZURE_SEARCH_INDEX, 
  "--documentintelligenceservice", $AZURE_DOCUMENT_INTELLIGENCE_SERVICE,
  "--documentintelligencekey", $AZURE_DOCUMENT_INTELLIGENCE_KEY,
  "--skipvectorization", $SEARCH_SKIP_VECTORIZATION,
  "--openAIService", $AZURE_OPENAI_EMBEDDINGS_SERVICE,
  "--openAIKey", $AZURE_OPENAI_EMBEDDINGS_API_KEY,
  "--openAIEngine", $AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME,
  "--openAITokenLimit", $AZURE_OPENAI_EMBEDDINGS_TOKEN_LIMIT,
  "--openAIDimensions", $AZURE_OPENAI_EMBEDDINGS_DIMENSIONS,
  "-v"


$process = Start-Process -FilePath $venvPythonPath -ArgumentList $predocsArguments -Wait -NoNewWindow -PassThru

if ($process.ExitCode -ne 0) {
  Write-Host ""
  Write-Warning "Document ingestion into search index failed with non-zero exit code $LastExitCode. This process must run successfully at least once for AI Search to behave properly."
  Write-Host ""
}
