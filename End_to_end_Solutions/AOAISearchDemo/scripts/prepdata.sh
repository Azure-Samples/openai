#!/bin/bash

# Set the Azure Key Vault details
KeyVaultName=""

echo ""
echo "Loading secrets from Azure Key Vault '$KeyVaultName' into environment..."
echo ""

# Install Azure CLI if not already installed
if ! command -v az &> /dev/null; then
    echo "Azure CLI not found. Installing..."
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
fi

# Log in to Azure
az login

# Set the environment variables
secrets=$(az keyvault secret list --vault-name $KeyVaultName --query "[].name" -o tsv)
for secret in $secrets; do
    value=$(az keyvault secret show --vault-name $KeyVaultName --name $secret --query "value" -o tsv)
    updatedName="${secret//-/_}"
    export $updatedName="$value"
done

# Log out from Azure
az logout

echo "Environment variables set."

venvPythonPath=$(which python)
if [ -z "$venvPythonPath" ]; then
    # Fallback to python3 if python not found
    venvPythonPath=$(which python3)
fi

echo 'Creating python virtual environment "scripts/.venv"'
$venvPythonPath -m venv ./scripts/.venv

venvPythonPath="./scripts/.venv/bin/python"
if [ -d "/usr" ]; then
    # Fallback to Linux venv path
    venvPythonPath="./scripts/.venv/scripts/python"
fi

echo 'Installing dependencies from "requirements.txt" into virtual environment'
$venvPythonPath -m pip install -r ./scripts/requirements.txt

echo 'Packaging app directory'
$venvPythonPath -m pip install -e ./app

echo 'Running "prepdocs.py"'
cwd=$(pwd)
$venvPythonPath ./scripts/prepdocs.py $cwd/data/surface_device_documentation/ \
    --storageaccount $AZURE_STORAGE_ACCOUNT \
    --container $AZURE_STORAGE_CONTAINER \
    --searchservice $AZURE_SEARCH_SERVICE \
    --index $AZURE_SEARCH_INDEX \
    --formrecognizerservice $AZURE_FORMRECOGNIZER_SERVICE -v

echo 'Running "prepopulate.py"'
$venvPythonPath ./scripts/prepopulate/prepopulate.py \
    --entities_path ./scripts/prepopulate/entries/entities.yaml \
    --permissions_path ./scripts/prepopulate/entries/permissions.yaml \
    --cosmos_db_endpoint $AZURE_COSMOS_ENDPOINT \
    --cosmos_db_key $AZURE_COSMOS_KEY \
    --cosmos_db_name $AZURE_COSMOS_DB_NAME \
    --cosmos_db_entities_container_name $AZURE_COSMOS_DB_ENTITIES_CONTAINER_NAME \
    --cosmos_db_permissions_container_name $AZURE_COSMOS_DB_PERMISSIONS_CONTAINER_NAME

echo 'Running "populate_sql.py"'
$venvPythonPath ./scripts/.venv/bin/python ./scripts/prepopulate/populate_sql.py --sql_connection_string $SQL_CONNECTION_STRING