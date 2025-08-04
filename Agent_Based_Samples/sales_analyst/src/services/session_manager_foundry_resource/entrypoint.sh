#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔐 Logging in to Azure..."

# Login using tenant ID
az login --tenant "$AZURE_TENANT_ID" --allow-no-subscriptions

# Set the desired subscription
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

echo "✅ Azure login successful. Starting application..."

# Run Session Manager application
exec python3 -u /src/session_manager_foundry_resource/app.py