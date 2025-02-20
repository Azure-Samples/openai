## SOLUTION CAPABILITIES

## Table of Contents

- [System Architecture](#system-architecture)
- [Microservice and AI Skills](#microservice-and-ai-skills)
  - [Ingestion Service](#ingestion-service)
  - [Search Service](#search-service)
  - [Session Manager](#session-manager) 
  - [Orchestrator](#orchestrator)
  - [Configuration Service](#configuration-service)
  - [Data Service](#data-service)
  - [AI skills](#ai-skills)
    - [Image Describer Skill](#image-describer-skill)
    - [Recommender Skill](#recommender-skill)
- [Sharing Intermediate Results](#sharing-intermediate-skill)
- [Architecture Features](#Architecture-features)
- [Secure Runtime and Deployment of Copilot](#secure-runtime-and-deployment-of-copilot)
  - [Security](#security)
  - [Composability](#composability)
  - [Iterability](#iterability)
  - [Logging and Instrumentation](#logging-and-instrumentation)

### SYSTEM ARCHITECTURE
![Architecture Diagram](./docs/media/retail_solution_architecture.png)

### Microservice and AI Skills

#### Ingestion Service
Ingestion service is a generic service that use different Azure AI services to enrich the content (chunks) as it indexes them to improve search quality.
For example, when indexing product catalog, it uses AzureOpenAI services to extract salient features of the product images and adds them to the index. This improves searching across product even better.

Have you experiences poor search results on retailer site specially for 3rd party market place products? We think this capability would drastically help improve search results across the board.

The ingestion process primarily consists of three steps: Image Encoding, Catalog Enrichment, and Catalog Indexing.

For more details refer ingestion service documentation [Ingestion Service](./src/skills/ingestion/README_RETAIL.md).

#### Search Service

Once the Ingestion pipeline is executed successfully resulting in a valid, queryable Search Index, the Search service can be configured and integrated into the end-to-end application. 

The Search Service exposes an API that enables users to query a search index in Azure AI Search. It processes natural language queries, applies requested filters, and invokes search requests against the preconfigured search configuration using the Azure AI Search SDK.  

For more details refer search service documentation [Search Skill](./src/skills/search/README_RETAIL.md).

#### Session Manager

Maintains the context of ongoing interactions by tracking conversation history and unique session IDs, ensuring continuity and coherence in multi-turn interactions. This is useful when user has follow up questions. Example: User has already honed down a product and would now like to get matching pair of clothing or accessory.

#### Orchestrator

The orchestrator service acts as the central controller, coordinating between various components: 

- Classifier: Determines if the query contains an image, audio, or text and categorizes the query as valid, invalid, or out of scope. It also uses the conversation history to rephrase the user query to capture the context of the user conversation.

- Skill Executor: Calls the appropriate skills based on the classified input and orchestrates the response generation process. 

- Final Answer Generator: Compiles the final answer based on the results from various skills and returns it to the user. 
 

#### Configuration Service

The runtime configuration service enhances the architecture's dynamicity and flexibility. It enables core services and AI skills to decouple and parameterize various components, such as prompts, search data settings, and operational parameters. These services can easily override default configurations with new versions at runtime, allowing for dynamic behavior adjustments during operation. The biggest benefit of the configuration service is its ability to expose different configurations for various microservices during runtime, making processes like evaluations much easier - no need for any more deployments. This could also be used to demo against different search indexes as well. Example: default index is the one that is with this repo. However you can bring your own product catalog and create a new Index and use that via runtime configuration. More details on how to configure the entire demo for your data is [here](./Setup.md/#build-your-own-copilot)

For more details refer config service documentation [Configuration Service](./src/config_hub/README.md).

#### Data Service

The Data Service is responsible for managing all database interactions related to chat sessions and user profiles. Its primary functionalities include:

- Chat Session Management:
  - Create: Initializes new chat sessions in the database.
  - Update: Updates ongoing chat sessions with new data, such as user inputs or system responses.
  - Get: Retrieves existing chat sessions based on session identifiers.
- User Profile Management:
  - Create: Adds new user profiles to the database, including user-specific information such as preferences or settings.
  - Get: Fetches details for a specific user profile based on user identifiers.
  - Get All: Retrieves a list of all user profiles stored in the system.

#### AI Skills
To ensure modularity and ease of maintenance, our solution designates any service capable of providing data as a "skill." This approach allows for seamless plug-and-play integration of components. For instance, Azure AI Search is treated as a skill within our architecture. Should the solution require additional data sources, such as a relational database, these can be encapsulated within an API and similarly integrated as skills.


##### Image Describer Skill

The Image Describer Skill generates detailed, one-sentence descriptions of user provided product images. This skill focuses on capturing all important and distinguishing features of the item in a clear and concise manner.

Key Features:
- Comprehensive Descriptions: Highlights critical attributes such as color, texture, materials, functionality, patterns, and unique details.
- Strictly Observational: Describes only what is visible in the image without including suggestions, recommendations, or inferred details.
- One-Sentence Output: Ensures each description is succinct yet thorough.

##### Recommender Skill

The Recommender Service transforms user-provided context into natural language search queries that the system uses to retrieve relevant products.

Key Features:
- Context-Aware Recommendations: Leverages both textual and visual input (e.g., descriptions of uploaded images) to provide tailored suggestions.
- Descriptive Search Queries: Converts user input into natural language queries that highlight essential product qualities like color, style, material, and occasion.
- Database-Agnostic: Works without prior knowledge of the database or its inventory, ensuring unbiased recommendations. 
- The prompt for the Recommender Skill can be found [here](./src/skills/recommender/src/prompts_config.yaml). It can be customized to include additional context, such as specific categories within the catalog or other relevant details, to ground the generated recommendations.

### Sharing Intermediate Results

The solution also supports sharing intermediate bot results, giving users insight into the bot's progress after submitting a query. This feature is particularly valuable for queries that take a long time to process. As soon as the user sends a query, the orchestrator provides updates like “Searching for...,” or “Retrieved XX results...” before delivering the final answer.

![Sharing Intermediate Results](./docs/media/sharing_intermediate_results.png)

The custom copilot project is designed to handle various tasks using a robust and scalable architecture. The architecture includes the following key aspects:

### Architecture Features

#### Security

- **User Authentication**: The solution uses Microsoft Entra ID for user authentication, ensuring secure access to the system.
- **Network Security**: All runtime components are locked behind a Virtual Network (VNet) to ensure that traffic does not traverse public networks. This enhances security by isolating the components from external threats.
- **Managed Identities**: The solution leverages managed identities where possible to simplify the management of secrets and credentials. This reduces the risk of credential exposure and makes it easier to manage access to Azure resources.

#### Composability

- **Modular Design**: The solution is broken down into smaller, well-defined core microservices and skills that act as plug-and-play components. This modular design allows you to use existing services or bring in new ones to meet your specific needs.
- **Core Microservices**: Backend services handle different aspects of the solution, such as session management, data processing, runtime configuration, and orchestration.
- **Skills**: Specialized services provide specific capabilities, such as Azure AI search and image processing. These skills can be easily integrated or replaced as needed.

#### Iterability

- **Configuration Service**: The solution includes a configuration service that allows you to create runtime configurations for each microservice. This enables you to make changes, such as updating prompts or search indexes, without redeploying the entire solution.
- **Per-User Prompt Configuration**: You can use the configuration service to apply different configurations for each user prompt, allowing for rapid experimentation and iteration. This flexibility helps you quickly adapt to changing requirements and improve the overall system.
- **Testing and Evaluation**: The solution also comes with the ability to run dummy/simulated conversations in the form of nightly runs, end-to-end integration tests on demand, and an evaluation tool to perform end-to-end evaluation of the copilot.

#### Logging and Instrumentation

- **Application Insights**: The solution integrates with Azure Application Insights for logging and instrumentation, making it easy to debug by reviewing logs.
- **Traceability**: You can trace what is happening in the backend using the `conversation_id` and `dialog_id` (unique GUIDs generated by the frontend) for each user session and interaction. This helps in identifying and resolving issues quickly.

### Secure Runtime and Deployment of Copilot

The architecture ensures that all components are protected within a virtual network, leveraging Azure services to maintain high security and performance. Key elements include:

- **Public Network Interaction**: Users access Copilot through a Bot Frontend, with API Management handling requests.
- **Microsoft Entra ID**: Helps manage identity and access control, ensuring secure authentication.
- **Azure DevOps**: Facilitates continuous integration and deployment, with Docker images stored in Azure Container Registry (ACR).
- **Secure Virtual Network**: The Azure Application Gateway manages incoming traffic, routing it to the Azure Kubernetes Service (AKS) cluster. The AKS cluster hosts essential services like Search and Ingestion, protected by a Network Security Group (NSG).
- **Endpoint Security**: Private endpoints connect to critical services like Key Vaults, Azure Storage, Cosmos DB, and Azure AI Services, ensuring data remains secure and private.

![Secure Runtime Architecture](./docs/media/secure_runtime.png)
More details on the securing the runtime infrastructure, check out the [secure_runtime_architecture.md](docs/secure_runtime_architecture.md) in the `/docs` folder.
