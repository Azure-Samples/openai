# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from typing import Optional, Union
import pandas as pd
from abc import abstractmethod

from azure.ai.projects.models import DatasetVersion
from azure.ai.evaluation import evaluate as azure_ai_evaluate
from common.agent_factory.agent_base import AzureAIAgentBase, ChatCompletionAgentBase, AzureAIFoundryAgentBase
from common.contracts.configuration.agent_config import (
    AIFoundryAgentConfig,
    ChatCompletionAgentConfig,
    AzureAIAgentConfig,
)
from common.evals.utils.evaluator_utils import get_agent_evaluators
from common.utilities.files import load_file
from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import EvaluationJobConfig
from common.contracts.configuration.orchestrator_config import (
    ResolvedOrchestratorConfig,
)
from common.evals.eval_types.eval_base import EvalBase
from common.evals.utils.agent_utils import create_kernel
from common.evals.utils.agent_utils import get_benchmark_answers


class AgentEvalBase(EvalBase):
    """
    Base class for agent evaluation.
    """

    def __init__(
        self,
        eval_config: EvaluationJobConfig,
        azure_openai_endpoint: str,
        azure_subscription_id: str,
        azure_resource_group: str,
        azure_workspace_name: str,
        logger: AppLogger,
        ai_project_endpoint,
        azure_openai_api_key,
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
        self.kernel = None
        self.agent_config: Union[AIFoundryAgentConfig, ChatCompletionAgentConfig, AzureAIAgentConfig] = None
        self.agent: Union[ChatCompletionAgentBase, AzureAIAgentBase, AzureAIFoundryAgentBase] = None

    async def get_service_and_agent_config(self) -> ResolvedOrchestratorConfig:
        config = load_file(self.eval_config.config_file_path, "yaml")
        return ResolvedOrchestratorConfig(**config)

    async def create_kernel_from_config(self, config: ResolvedOrchestratorConfig) -> None:
        self.kernel = create_kernel(config=config)

    @abstractmethod
    async def create_agent_from_config(self, config: Optional[ResolvedOrchestratorConfig] = None) -> None:
        """
        Create an agent from the provided configuration.
        Must be implemented by child classes.

        Args:
            config: Configuration object containing agent details
        """
        pass

    async def get_responses(self, benchmark_questions: pd.DataFrame, run_dir_path: str) -> pd.DataFrame:
        """
        Get responses from the agent for the provided benchmark questions.

        Args:
            benchmark_questions: DataFrame containing the evaluation dataset
            run_dir_path: Path to the directory for saving evaluation results

        Returns:
            DataFrame containing the agent's responses
        """
        if self.agent is None:
            raise ValueError("Agent is not created. Please call create_agent_from_config first.")
        if self.agent_config is None:
            raise ValueError("Agent configuration is not set. Please call create_agent_from_config first.")

        return await get_benchmark_answers(
            agent=self.agent,
            agent_config=self.agent_config,
            benchmark_questions=benchmark_questions,
            azure_ai_client=self.project_client,
            kernel=self.kernel,
            run_dir_path=run_dir_path,
        )

    async def run_local_evaluation(self, experiment_id: str, eval_data_path: str) -> str:
        """
        Run local evaluation using agent-specific evaluators. If no agent evaluators are found, skip local evaluation.
        """

        agent_evaluators = get_agent_evaluators(
            evaluators_config=self.eval_config.metric_config,
            azure_openai_endpoint=self.azure_openai_endpoint,
        )

        if not agent_evaluators:
            self.logger.warning("No evaluators found specific to agents. Skipping local evaluation.")
            return

        self.logger.info(f"Running local evaluation with evaluators: {list(agent_evaluators.keys())}")
        response = azure_ai_evaluate(
            evaluation_name=f"{experiment_id}_local_eval",
            data=eval_data_path,
            evaluators=agent_evaluators,
            azure_ai_project={
                "subscription_id": self.azure_subscription_id,
                "project_name": self.azure_workspace_name,
                "resource_group_name": self.azure_resource_group,
            },
        )
        return response.get("studio_url")

    async def evaluate(self):
        """
        Main evaluation workflow that orchestrates all evaluation steps.
        """

        try:
            # Load dataset
            benchmark_questions = await self.load_evaluation_dataset()
            resolved_config = None
            if self.eval_config.config_file_path:
                resolved_config = await self.get_service_and_agent_config()
                if resolved_config.service_configs:
                    await self.create_kernel_from_config(resolved_config)

            await self.create_agent_from_config(resolved_config)
            if isinstance(self.agent, AzureAIFoundryAgentBase):
                agent_name = self.agent_config.name if self.agent_config else "Unknown Agent"
            else:
                # For ChatCompletionAgentBase and AzureAIAgentBase, use agent_config's agent_name
                agent_name = self.agent_config.agent_name if self.agent_config else "Unknown Agent"
            # Create experiment ID
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M%S")
            experiment_id = f"Agent-Eval_Agent_eq_{agent_name}_Start_eq_{current_time}"
            run_dir_path = f"{os.path.dirname(__file__)}/../results/{experiment_id}"
            os.makedirs(run_dir_path, exist_ok=True)

            # Run agent-specific evaluation
            benchmark_answers_save_path = await self.get_responses(benchmark_questions, run_dir_path)

            # Upload results
            try:
                benchmark_data: DatasetVersion = await self.project_client.datasets.upload_file(
                    name=f"{experiment_id}_benchmark_answers",
                    version="1.0",
                    file_path=benchmark_answers_save_path,
                )
            except Exception as e:
                self.logger.error(f"Failed to upload file: {e}")
                return

            # Run local evaluation if configured for agent evaluators
            local_eval_results_url = await self.run_local_evaluation(experiment_id, benchmark_answers_save_path)

            # Run evaluation and get results URL
            results_url = await self.run_ai_foundry_evaluation(benchmark_data.id, experiment_id)

            if results_url:
                self.logger.info(f"\nEvaluation run complete. Use AI project URI for detailed metrics: {results_url}")
            if local_eval_results_url:
                self.logger.info(f"Local evaluation results available at: {local_eval_results_url}")

        finally:
            # Cleanup
            if self.project_client:
                await self.project_client.close()
