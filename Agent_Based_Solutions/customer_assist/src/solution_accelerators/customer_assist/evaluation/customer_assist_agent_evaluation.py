# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
import sys
import os
# Correct the path to include the orchestrator module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'orchestrator')))

from common.evals.eval_types.agent_eval_base import AgentEvalBase
from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import EvaluationJobConfig
from orchestrator.agents.agent_factory import CustomerCallAssistAgentFactory

class AgentType(Enum):
    """
    Enum representing the different types of agents in the Customer Assist solution.
    """
    ASSIST = "ASSIST_AGENT"
    SENTIMENT_ANALYSIS = "SENTIMENT_ANALYSIS_AGENT"
    POST_CALL_ANALYSIS = "POST_CALL_ANALYSIS_AGENT"

class CustomerAssistAgentEval(AgentEvalBase):
    """
    Evaluation class for Customer Assist agents.
    Inherits from the base AgentEval class and implements customer-call-assist-specific agent creation and execution.
    """
    def __init__(
            self,
            eval_config: EvaluationJobConfig,
            ai_project_conn_str: str, 
            azure_openai_endpoint: str,
            azure_subscription_id: str, 
            azure_resource_group: str, 
            azure_workspace_name: str,
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
        self.agent_factory = None

    async def create_agent_from_config(self, config):
        self.agent_factory = await CustomerCallAssistAgentFactory.get_instance()
        await self.agent_factory.__init_async__(self.logger)

        agents_config = config.agent_configs

        if self.eval_config.agent_config_id not in agents_config:
            raise ValueError(f"Agent {self.eval_config.agent_config_id} not found in the provided configs.")
        self.agent_config = agents_config[self.eval_config.agent_config_id].config_body
        self.agent_name = self.agent_config.agent_name

        agent_type = AgentType(self.eval_config.agent_config_id)
        self.logger.info(f"Creating agent: {agent_type.name}")

        try:
            if agent_type == AgentType.ASSIST:
                self.agent = await self.agent_factory.get_assistant_agent(
                    kernel=self.kernel,
                    configuration=self.agent_config
                )
                self.agent_instructions = self.agent_config.azure_ai_agent_config.instructions
            elif agent_type == AgentType.SENTIMENT_ANALYSIS:
                self.agent = await self.agent_factory.get_sentiment_agent(
                    kernel=self.kernel,
                    configuration=self.agent_config
                )
                self.agent_instructions = self.agent_config.prompt
            elif agent_type == AgentType.POST_CALL_ANALYSIS:
                self.agent = await self.agent_factory.get_post_call_agent(
                    kernel=self.kernel,
                    configuration=self.agent_config
                )
                self.agent_instructions = self.agent_config.azure_ai_agent_config.instructions
            else:
                raise ValueError(f"Unsupported agent type: {agent_type}")
            
            self.logger.info(f"{agent_type.name} created successfully.")
        except ValueError as e:
            self.logger.error(f"Error creating agent: {e}")
            raise
