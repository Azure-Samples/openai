# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from enum import Enum
import os
import sys
from typing import Optional

from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from common.utilities.files import load_file

# Add the parent directory to the Python path so we can import from agents and common
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from azure.monitor.opentelemetry import configure_azure_monitor
from common.telemetry.app_logger import AppLogger
from common.telemetry.app_tracer_provider import AppTracerProvider
from opentelemetry import trace

from common.evals.eval_types.agent_eval_base import AgentEvalBase
from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import AgentEvaluation, EvaluationJobConfig, EvaluationsConfig
from config.default_config import DefaultConfig
from agents.sharepoint_agent import SharePointAgent

DefaultConfig.initialize()

# Set up logging and tracing
appinsights_connection_string = DefaultConfig.APPLICATION_INSIGHTS_CNX_STR
tracer_provider = AppTracerProvider(appinsights_connection_string)
tracer_provider.set_up()
tracer = trace.get_tracer(__name__)
logger = AppLogger(appinsights_connection_string)


default_runtime_config = load_file(
    os.path.join(
        os.path.dirname(__file__),
        "static",
        "eval_config.yaml",
    ),
    "yaml",
)


class AgentType(Enum):
    """
    Enum representing the different types of agents in the solution.
    """

    SHAREPOINT_AGENT = "SHAREPOINT_AGENT"


class AgentEval(AgentEvalBase):
    """
    Evaluation class for Customer Assist agents.
    Inherits from the base AgentEval class and implements customer-call-assist-specific agent creation and execution.
    """

    def __init__(
        self,
        eval_config: EvaluationJobConfig,
        ai_project_endpoint: str,
        azure_openai_endpoint: str,
        azure_subscription_id: str,
        azure_resource_group: str,
        azure_workspace_name: str,
        logger: AppLogger,
        azure_openai_api_key: Optional[str] = None,
    ):
        super().__init__(
            eval_config=eval_config,
            ai_project_endpoint=ai_project_endpoint,
            azure_openai_endpoint=azure_openai_endpoint,
            azure_subscription_id=azure_subscription_id,
            azure_resource_group=azure_resource_group,
            azure_workspace_name=azure_workspace_name,
            logger=logger,
            azure_openai_api_key=azure_openai_api_key,
        )

    async def create_agent_from_config(self, config: ResolvedOrchestratorConfig) -> None:
        agent_type = AgentType(self.eval_config.agent_config_id.upper())
        self.logger.info(f"Creating agent: {agent_type.name}")

        try:
            if agent_type == AgentType.SHAREPOINT_AGENT:
                agent_config = config.agent_configs[self.eval_config.agent_config_id].config_body
                sharepoint_agent: SharePointAgent = await SharePointAgent.get_instance(
                    logger=self.logger,
                )

                await sharepoint_agent.initialize(
                    sharepoint_connection_name=os.getenv("SHAREPOINT_CONNECTION_NAME"),
                    project_client=self.project_client,
                    configuration=agent_config,
                )

                self.agent = sharepoint_agent
                self.agent_config = agent_config
            else:
                raise ValueError(f"Unsupported agent type: {agent_type}")

            self.logger.info(f"{agent_type.name} created successfully.")
        except ValueError as e:
            self.logger.error(f"Error creating agent: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating agent: {e}")
            raise


async def main():
    eval_jobs_config = EvaluationsConfig(**default_runtime_config)

    eval_name = input("Enter the evaluation name: ")

    if eval_name not in eval_jobs_config.evaluation_jobs:
        logger.error(f"Invalid evaluation name: {eval_name}")
        return

    current_eval_config = eval_jobs_config.evaluation_jobs[eval_name].config_body

    if isinstance(current_eval_config, AgentEvaluation):
        agent_eval_job = AgentEval(
            eval_config=current_eval_config,
            azure_openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
            azure_subscription_id=DefaultConfig.AZURE_SUBSCRIPTION_ID,
            azure_resource_group=DefaultConfig.AZURE_RESOURCE_GROUP,
            azure_workspace_name=DefaultConfig.AZURE_WORKSPACE_NAME,
            ai_project_endpoint=DefaultConfig.AZURE_AI_AGENT_ENDPOINT,
            logger=logger,
            azure_openai_api_key=DefaultConfig.AZURE_OPENAI_KEY,
        )
        await agent_eval_job.evaluate()


asyncio.run(main())
