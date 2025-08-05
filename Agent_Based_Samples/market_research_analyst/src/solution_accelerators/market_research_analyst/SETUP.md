# Market Research Analyst Setup Instructions

## Overview

The Market Research Analyst solution setup requires initialization of four key agents:

- **Search Query Generator Agent**
- **Researcher Agent**
- **Report Generator Agent**
- **Report Comparator Agent**

All four agents run in Azure AI Foundry serverless instance. For more information on Azure AI Foundry Agent service, refer to the link at the bottom of the instructions.

## Prerequisites

Before setting up the solution, ensure the following:

1. **System Requirements**:
    - Operating System: Windows (can be extended to Linux)
    - Python 3.12 or higher installed
    - [Visual Studio Code](https://code.visualstudio.com/)
    - [Python VSCode Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
    - **Docker** runtime installed to run a Redis container (Redis acts as a message broker in the backend system)

      To run a Redis container locally using Docker, you can use the following bash script:

      ```bash
      #!/bin/bash

      # Pull the latest Redis image from Docker Hub
      docker pull redis:latest

      # Run the Redis container
      docker run --name redis-container -d -p 6379:6379 redis:latest

      # Verify if the container is running
      docker ps | grep redis-container
      ```

      This will start a Redis container named `redis-container` and expose it on port `6379` for local development.

2. **Access Credentials**:
    - RBAC Access to `Grounding with Bing Search`
    - `Search Index Data Contributor` role assignment on `Azure AI Search` resource

3. **Dependencies**:
    - Azure AI Foundry Agent Service (more details can be found here: [Azure AI Foundry Agent Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview))
    - Required Python libraries (see `requirements.txt` for package and version information)

---

## Setup Instructions

### Local Development Setup & Execution Guide (VSCode)

This guide outlines the steps to set up and run the **Market Research Analyst** service locally using Visual Studio Code (VSCode). It leverages VSCode's task and launch configurations (`tasks.json` and `launch.json`) to automate environment preparation and service startup.

---

## ⚙️ Project Structure

```
root/
│
├── .vscode/
│   ├── launch.json                                # VSCode launch configuration
│   └── tasks.json                                 # VSCode task configuration
├── src/                                           # Project source code
    ├── agents/                                    # Core Agents
        ├── search_query_generator_agent
        ├── researcher_agent
        ├── report_generator_agent
        └── report_comparator_agent
    ├── evaluation/                                # Agent and end-to-end evaluations
    ├── frontend/                                  # A simple web UI to interact with Market Research Analyst
        └── index.html
    ├── orchestrator/                              # Agent orchestration layer
        └── agent_orchestrator
    ├── requirements.txt                           # Python dependencies
    ├── LICENSE                                    # MIT License
    ├── README.md                                  # High-level overview of the solution
    ├── SETUP.md                                   # Setup instructions
    └── MarketResearchAnalyst_Architecture.png     # Architecture Diagram
```

## 🚀 Running the Service Locally (VSCode) [OPTIONAL]

**For best experience, use Docker execution:** [Docker Execution in Local](../../DOCKER.README.md)

Alternatively, the service can be launched and debugged directly via VSCode using the predefined launch configuration.

### ✅ Steps

1. Press `Ctrl+Shift+D` or go to the **Run and Debug** tab in VSCode.
2. Select the launch configuration:

   ```
   Session Manager: Launch & Attach server
   ```

   followed by

   ```
   Market Research Analyst: Launch & Attach server
   ```

3. Click the green **Run** button or press `F5`.

This launch task will:

- Automatically create and activate a Python virtual environment (if not already created).
- Install required dependencies via `pip install -r requirements.txt`.
- Load environment variables from the `.env` file.
- Start all required background services and dependencies (`Session Manager`).
- Launch and attach to the main service process for debugging.

---

## 🧪 Verifying the Setup

After launch, check the VSCode terminal and Debug Console for:

- Confirmation that the server is running
- Logs from supporting services
- Any errors or missing dependencies

---

## 📄 Stopping the Service

To stop the running service and all its dependencies:

1. Press `Ctrl+C` in the VSCode terminal (if services run there), or
2. Press the **Stop** button in the Debug panel

---

## 📝 Notes

- To add new environment variables, update the `.env` file and restart the service.
- If the virtual environment setup fails, try deleting the `.venv` folder and rerun the launch task.

---

## 📂 Related Files

- `.vscode/launch.json`: Contains the main launch configuration.
- `.vscode/tasks.json`: Contains all prerequisite tasks and automation scripts.

---

## Troubleshooting

- **Researcher Agent or Report Comparator Issues**: Ensure that Grounding with Bing Search connection is added successfully into Azure AI Foundry.
- **Report Save/Retrieval Issues**: Ensure that there is a valid role assignment in Azure AI Search for your identity to be able to save current report and/or retrieve existing reports.
- To create a new project, follow instructions here: [Create Azure AI Foundry Project](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects).

---

Market Research Analyst should be up and running 🚀
