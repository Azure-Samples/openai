Write-Host "Restoring frontend npm packages"
Write-Host ""
Set-Location ./backend/frontend
npm install
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to restore frontend npm packages"
  Set-Location ../..
  exit $LASTEXITCODE
}

Write-Host "Building frontend"
Write-Host ""
npm run build
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to build frontend"
  Set-Location ../..
  exit $LASTEXITCODE
}

Set-Location ../..
& "../scripts/createEnv.ps1" -Path "./data"
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to create data service python virtual environment"
  exit $LASTEXITCODE
}

& "../scripts/createEnv.ps1" -Path "./skills/search"
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to create search skill python virtual environment"
  exit $LASTEXITCODE
}

& "../scripts/createEnv.ps1" -Path "./skills/sql"
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to create SQL skill python virtual environment"
  exit $LASTEXITCODE
}

& "../scripts/createEnv.ps1" -Path "./orchestrator"
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to create orchestrator service python virtual environment"
  exit $LASTEXITCODE
}

& "../scripts/createEnv.ps1" -Path "./backend"
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to create backend service python virtual environment"
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Restoring data service python packages"
Write-Host ""

$venvPythonPath = ".venv/Scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = ".venv/bin/python"
}

Start-Process -FilePath "./data/$venvPythonPath" -ArgumentList "-m pip install --use-feature=in-tree-build -r data/requirements.txt" -Wait -NoNewWindow
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to restore data service python packages"
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Restoring search skill python packages"
Write-Host ""

Set-Location ./skills
Start-Process -FilePath "./search/$venvPythonPath" -ArgumentList "-m pip install --use-feature=in-tree-build -r search/requirements.txt" -Wait -NoNewWindow
Set-Location ..
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to restore search skill python packages"
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Restoring SQL skill python packages"
Write-Host ""

Set-Location ./skills
Start-Process -FilePath "./sql/$venvPythonPath" -ArgumentList "-m pip install --use-feature=in-tree-build -r sql/requirements.txt" -Wait -NoNewWindow
Set-Location ..
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to restore SQL skill python packages"
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Restoring orchestrator service python packages"
Write-Host ""

Start-Process -FilePath "./orchestrator/$venvPythonPath" -ArgumentList "-m pip install --use-feature=in-tree-build -r orchestrator/requirements.txt" -Wait -NoNewWindow
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to restore orchestrator service python packages"
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Restoring backend service python packages"
Write-Host ""

Start-Process -FilePath "./backend/$venvPythonPath" -ArgumentList "-m pip install --use-feature=in-tree-build -r backend/requirements.txt" -Wait -NoNewWindow
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to restore backend service python packages"
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Starting data service"
Write-Host ""
Set-Location ./data
Start-Process -FilePath "./$venvPythonPath" -ArgumentList "app.py" -NoNewWindow
Set-Location ..
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to start data service"
  exit $LASTEXITCODE
}

Write-Host "Starting search skill"
Write-Host ""
Set-Location ./skills/search
Start-Process -FilePath "./$venvPythonPath" -ArgumentList "app.py" -NoNewWindow
Set-Location ../..
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to start search skill"
  exit $LASTEXITCODE
}

Write-Host "Starting SQL skill"
Write-Host ""
Set-Location ./skills/sql
Start-Process -FilePath "./$venvPythonPath" -ArgumentList "app.py" -NoNewWindow
Set-Location ../..
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to start SQL skill"
  exit $LASTEXITCODE
}

Write-Host "Starting orchestrator"
Write-Host ""
Set-Location ./orchestrator
Start-Process -FilePath "./$venvPythonPath"  -ArgumentList "app.py" -NoNewWindow
Set-Location ..

if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to start orchestrator"
  exit $LASTEXITCODE
}

Write-Host "Starting backend"
Write-Host ""
Set-Location ./backend
Start-Process -FilePath "./$venvPythonPath" -ArgumentList "app.py" -NoNewWindow
Set-Location ..
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to start backend"
  exit $LASTEXITCODE
}
Start-Process http://127.0.0.1:5000