<div align="center">
  <h1>
    Release Manager
  </h1>
  <p><strong>Transforming software delivery process with intelligent agent orchestration</strong></p>
  <br>
  <p><a href="https://github.com/user-attachments/assets/6c8202bf-9d7b-4aaf-9907-81124adaaa9d">▶️ Watch Intro Video</a></p>
</div>

## 🚀 Overview

In modern software development, **Release Managers** play a pivotal role bridging the gap between development and operations. As the orchestrators of software deployment, they ensure that releases are timely, efficient, and risk-mitigated. However, increasing complexity and fragmentation across systems have made this role more challenging than ever.

The **Release Manager Assistant (RMA)** is a solution accelerator designed to augment release managers with AI-driven intelligence, multi-system integration, and real-time decision support. It simplifies the release lifecycle from planning to post-deployment analysis, all through a unified and contextual interface.

Watch a quick demo below!

<p><a href="https://github.com/user-attachments/assets/fad365a9-f777-4aae-80e4-a437c5ad50e7">▶️ Demo Video</a></p>
---

## 🧩 Key Challenges

- Fragmented release data across platforms
- Lack of real-time release health visibility
- High manual effort in compiling readiness reports
- Difficulty managing cross-team/service dependencies
- Visualizing complex data across multiple systems
- Notifying stakeholders on change in the system

---

## ✅ What the RMA Solves

### 🔄 Release Planning & Coordination

- Real-time dependency mapping and release health assessment
- Visualization of complex data

### 🕓 Scheduling & Readiness Automation

- Smart notifications
- Issue and stakeholder updates via integrated channels (emails)

### 🌐 Cross-System Collaboration

- Seamless integration with tools like:
  - JIRA
  - DevOps (MySQL database and/or API integration)
  - Microsoft Graph APIs
- Unified, contextual insights from disparate systems

---

## 🧠 Solution Architecture

The architecture is built on a modular and secure AI-native design leveraging:

- **Azure AI Foundry service** for agents in cloud and supporting tools (Code Interpreter).
- **Semantic Kernel** for agent orchestration, agent memory and tools integration.
- **Microsoft Graph API** for enterprise identity and email notification integration*.
- **Azure Key Vault & Azure Storage** for secure secret and data management.

*For setting up email notifications, additional setup is required. For instructions, please refer to this guide: [Microsoft Email Notifications Setup](src/solution_accelerators/release_manager/plugins/NOTIFICATIONS.md)*

### 🎯 Architecture Walkthrough

https://github.com/user-attachments/assets/619f5a11-45ed-4a8b-a2e4-7d3900eee60e


---

### 📐 Architecture Diagram

This diagram provides a visual representation of how the **JIRA Agent**, **DevOps Agent**, **Visualization Agent** and **Notification Agent** collaborate to streamline release planning and execution for a release manager.

![RMA Solution Architecture](src/solution_accelerators/release_manager/ReleaseManagerAssistant_Architecture.png)

*Diagram above highlights components in the end-to-end system run that run locally (highlighted in green) and components that run in the cloud (highlighted in blue).*

---

## 🛠️ Getting Started

> **Note**: This solution accelerator is designed to be adaptable. You can customize integrations and workflows based on your internal tooling landscape.

For detailed setup instructions, please follow the guide here: [SETUP INSTRUCTIONS](src/solution_accelerators/release_manager/SETUP.md)

### Prerequisites

- Azure Subscription
- Access to Azure OpenAI and Azure AI Foundry
- Local/Cloud instance for JIRA, DevOps (MySQL connection), etc.
- python >= 3.12
- Docker runtime for running service containers locally (For more information on local execution, refer to this guide: [LOCAL EXECUTION IN DOCKER](src/DOCKER.README.md))

---

## 🔗 Integrations Supported

- [JIRA SDK](https://jira.readthedocs.io/)
- [JIRA API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/overview)
- [MySQL](https://dev.mysql.com/)

*Synthetic dataset is included in the solution under `/data` directory for reference purposes.*

---

## 📈 Roadmap (subject to change)

- ✅ Multi-system integration baseline
- ✅ Natural language release query support
- 🚧 Azure DevOps integration
- 🚧 Teams notifications support

---

## Dataset License

The [dataset](data/) in this project is released under the Community Data License Agreement – Permissive, Version 2.0 - CDLA, see the [LICENSE-DATA](LICENSE-DATA.md) file.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

## 📚 Additional Resources

- [Azure AI Foundry Agent Service](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview)
- [Semantic Kernel Agent Framework](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/?pivots=programming-language-python)
- [Semantic Kernel Memory](https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors/?pivots=programming-language-python)
- [Azure AI Foundry - Code Interpreter](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/code-interpreter)
