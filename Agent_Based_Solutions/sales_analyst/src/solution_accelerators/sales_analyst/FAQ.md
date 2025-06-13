# Sales Analyst Solution: Frequently Asked Questions

This document addresses common issues and questions that might arise when setting up and running the Sales Analyst solution.

## Docker Container Issues

### Q: I'm getting an error: `exec /src/sales_analyst/orchestrator/entrypoint.sh: no such file or directory`

**A:** This error occurs when Docker cannot find or execute the entrypoint.sh file in the container, usually due to incorrect line endings or file permissions. To fix this:

1. **Convert line endings from Windows (CRLF) to Unix (LF):**

   Using PowerShell:
   ```powershell
   $content = Get-Content -Path ".\src\solution_accelerators\sales_analyst\orchestrator\entrypoint.sh" -Raw
   $content = $content -replace "`r`n", "`n"
   [System.IO.File]::WriteAllText(".\src\solution_accelerators\sales_analyst\orchestrator\entrypoint.sh", $content)
   ```

   Or you can use VS Code:
   - Open the file in VS Code
   - Click on "CRLF" in the bottom right status bar
   - Select "LF" to convert line endings
   - Save the file

2. **Ensure file permissions are correct in your Dockerfile:**
   ```dockerfile
   COPY solution_accelerators/sales_analyst/orchestrator/entrypoint.sh /src/sales_analyst/orchestrator/entrypoint.sh
   RUN chmod +x /src/sales_analyst/orchestrator/entrypoint.sh
   ```

3. **Rebuild your Docker container:**
   ```powershell
   # Use the VS Code task or run:
   ./src/Run-SolutionAcceleratorInDocker.ps1 -SolutionName SalesAnalyst -Recreate
   ```

## Authentication Issues

### Q: The Docker container is failing to authenticate with Azure

**A:** When running the Docker containers, each one needs to authenticate with Azure. Look for the authentication prompt in the container logs:

```
🔐 Logging in to Azure...

To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code ABCDEFG to authenticate.
```

1. Open a web browser and navigate to the URL shown (https://microsoft.com/devicelogin)
2. Enter the unique code displayed in the logs
3. Complete the Microsoft authentication process using your Azure credentials

## Environment Configuration

### Q: How do I update the Azure subscription and tenant IDs?

**A:** Edit the `.vscode/tasks.json` file to update the subscription ID and tenant ID in the Docker run tasks:

```json
"args": [
    "-SubscriptionId", 
    "your-subscription-id-here",
    "-TenantId",
    "your-tenant-id-here"
]
```

### Q: My .env files are not properly configured

**A:** Make sure all required environment variables are filled in each .env file. Refer to the SETUP.md file for detailed information about the required variables for each service.

## Connectivity Issues

### Q: The Web Interface cannot connect to the backend services

**A:** Ensure that:
1. All Docker containers are running
2. The ports are correctly mapped:
   - Session Manager: 5000
   - Orchestrator: 5102
3. The frontend is properly configured to connect to these services in its .env file

## Performance Issues

### Q: The agent responses are very slow

**A:** This could be due to:
1. Azure service throttling - check your Azure resource usage
2. Insufficient resources allocated to Docker - increase memory/CPU in Docker Desktop settings
3. Network latency - ensure you have a stable internet connection

## Azure AI Foundry Rate Limits

### Q: Are there rate limits I should be aware of?

**A:** Yes, Azure AI Foundry implements rate limits at different levels:

- Model inference limits (RPM and TPM)
- Content Understanding service limits
- API call frequency limits

These limits may impact your application's performance, especially during high traffic periods. For comprehensive information about specific quotas and limits, refer to the [Azure AI Foundry documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/quotas-limits).

## Additional Help

If you continue experiencing issues not addressed in this FAQ, please:

1. Check the Docker container logs for more specific error messages
2. Verify all Azure resources are correctly created and accessible
3. Ensure your Azure account has the necessary permissions as outlined in the SETUP.md file