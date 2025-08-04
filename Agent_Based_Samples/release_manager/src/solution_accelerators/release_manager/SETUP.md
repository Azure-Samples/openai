# Release Manager Assistant Setup Instructions

## Overview

The Release Manager solution is designed to assist in decision-making for software delivery releases by integrating three key agents:

- **JIRA Agent**: Fetches and processes data from JIRA backend to track issues, including custom fields. Agent has access to make changes in the JIRA system.
- **DevOps Agent**: Interfaces with MySQL database to retrieve current release status.
- **Visualization Agent**: Provides actionable insights and visual representations of release progress and associated tasks.

By combining these agents, the Release Manager enables streamlined release planning and execution.

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
    - JIRA system username and password
    - DevOps Database access credentials

3. **Dependencies**:
    - Azure AI Foundry Agent Service (more details can be found here: [Azure AI Foundry Agent Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview))
    - Required Python libraries (see `requirements.txt` under `/src` folder)

---

## Setup Instructions

### Local Development Setup & Execution Guide (VSCode)

This guide outlines the steps to set up and run the **Release Manager** service locally using Visual Studio Code (VSCode). It leverages VSCode's task and launch configurations (`tasks.json` and `launch.json`) to automate environment preparation and service startup.

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
        ├── jira_agent
        ├── devops_agent
        ├── visualization_agent
        └── notification_agent
    ├── evaluation/                                # Agent and end-to-end evaluations
    ├── frontend/                                  # A simple web UI to query Release Manager
        └── index.html
    ├── orchestrator/                              # Agent orchestration layer
        └── agent_orchestrator
    ├── plugins/                                   # Core Agent Plugins
        ├── jira_plugin
        ├── devops_plugin
        └── notification_plugin
    ├── requirements.txt                           # Python dependencies
    ├── LICENSE                                    # MIT License
    ├── README.md                                  # High-level overview of the solution
    ├── SETUP.md                                   # Setup instructions
    └── Synopsys_Agent_Architecture.png            # Architecture Diagram
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
   Release Manager: Launch & Attach server
   ```
3. Click the green **Run** button or press `F5`.

This launch task will:

* Automatically create and activate a Python virtual environment (if not already created).
* Install required dependencies via `pip install -r requirements.txt`.
* Load environment variables from the `.env` file.
* Start all required background services and dependencies (`Session Manager`).
* Launch and attach to the main service process for debugging.

---

## 🧪 Verifying the Setup

After launch, check the VSCode terminal and Debug Console for:

* Confirmation that the server is running
* Logs from supporting services
* Any errors or missing dependencies


---

## 📄 Stopping the Service

To stop the running service and all its dependencies:

1. Press `Ctrl+C` in the VSCode terminal (if services run there), or
2. Press the **Stop** button in the Debug panel

---

## 📝 Notes

* To add new environment variables, update the `.env` file and restart the service.
* If the virtual environment setup fails, try deleting the `.venv` folder and rerun the launch task.

---

## 📂 Related Files

* `.vscode/launch.json`: Contains the main launch configuration.
* `.vscode/tasks.json`: Contains all prerequisite tasks and automation scripts.

---

## Troubleshooting

- **JIRA Agent Issues**: Ensure that Jira service endpoint is accessible in the network and that the username and the password are correct.
- **DevOps Agent Issues**: Verify database access credentials are correct and that the user account used to interact with database has all required permissions.
- **Visualization Issues**: Ensure that connection to Azure AI Foundry is established successfully. Note that this agent requires an existing Azure AI Hub and Project in Azure AI Foundry.

To create a new project, follow instructions here: [create Azure AI Foundry Project](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects).

---

Release Manager should be up and running 🚀
