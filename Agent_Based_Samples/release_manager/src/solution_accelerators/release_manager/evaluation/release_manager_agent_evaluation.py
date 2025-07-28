# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import sys
import os
# Correct the path to include the modules needed for the Release Manager Agent Creation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.evals.eval_types.agent_eval_base import AgentEvalBase
from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import EvaluationJobConfig
from solution_accelerators.release_manager.agents.agent_factory import ReleaseManagerAgentFactory
from solution_accelerators.release_manager.models.agents import Agent
from solution_accelerators.release_manager.models.jira_settings import JiraSettings
from solution_accelerators.release_manager.models.devops_settings import DevOpsSettings

class ReleaseManagerAgentEval(AgentEvalBase):
    """
    Release Manager Agent Evaluation class.
    Inherits from the base AgentEval class and implements release_manager-specific agent creation and execution
    """
    def __init__(
            self,
            eval_config: EvaluationJobConfig,
            ai_project_conn_str: str, 
            azure_openai_endpoint: str,
            azure_subscription_id: str, 
            azure_resource_group: str, 
            azure_workspace_name: str,
            jira_settings: JiraSettings,
            devops_settings: DevOpsSettings,
            logger: AppLogger
    ):
        super().__init__(
            eval_config=eval_config,
            ai_project_conn_str=ai_project_conn_str,
            azure_openai_endpoint=azure_openai_endpoint,
            azure_subscription_id=azure_subscription_id,
            azure_resource_group=azure_resource_group,
            azure_workspace_name=azure_workspace_name,
            logger=logger
        )
        self.jira_settings = jira_settings
        self.devops_settings = devops_settings
        self.agent_factory = None

    async def create_agent_from_config(self, config):
        self.agent_factory = await ReleaseManagerAgentFactory.get_instance()
        await self.agent_factory.initialize(logger=self.logger, project_client=self.azure_ai_client)

        agents_config = config.agent_configs

        if self.eval_config.agent_config_id not in agents_config:
            raise ValueError(f"Agent {self.eval_config.agent_config_id} not found in the provided configs.")
        self.agent_config = agents_config[self.eval_config.agent_config_id].config_body
        self.agent_name = self.agent_config.agent_name

        agent_type = Agent(self.eval_config.agent_config_id)
        self.logger.info(f"Creating agent: {agent_type.name}")

        try:
            if agent_type == Agent.PLANNER_AGENT:
                self.agent = await self.agent_factory.create_planner_agent(
                    kernel=self.kernel,
                    configuration=self.agent_config
                )
                self.agent_instructions = self.agent_config.azure_ai_agent_config.instructions
            elif agent_type == Agent.JIRA_AGENT:
                self.agent = await self.agent_factory.create_jira_agent(
                    kernel=self.kernel,
                    configuration=self.agent_config,
                    jira_settings=self.jira_settings
                )
                self.agent_instructions = self.agent_config.prompt
            elif agent_type == Agent.DEVOPS_AGENT:
                self.agent = await self.agent_factory.create_devops_agent(
                    kernel=self.kernel,
                    configuration=self.agent_config,
                    devops_settings=self.devops_settings
                )
                self.agent_instructions = self.agent_config.prompt
            else:
                raise ValueError(f"Unsupported agent type: {agent_type}")
            
            self.logger.info(f"{agent_type.name} created successfully.")
        except ValueError as e:
            self.logger.error(f"Error creating agent: {e}")
            raise