# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import pandas as pd
from abc import abstractmethod

from azure.identity import DefaultAzureCredential
from azure.ai.evaluation import evaluate

from semantic_kernel.agents import AzureAIAgent

from common.utilities.files import load_file
from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import EvaluationJobConfig
from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from evals.eval_types.eval_base import EvalBase
from evals.utils.agent_utils import create_kernel
from evals.utils.agent_utils import get_benchmark_answers
from evals.utils.evaluator_utils import get_agent_evaluators

class AgentEvalBase(EvalBase):
    """
    Base class for agent evaluation.
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
        self.azure_ai_client = AzureAIAgent.create_client(
            credential=DefaultAzureCredential(),
            conn_str=self.ai_project_conn_str
        )
        self.kernel = None
        self.agent_config = None
        self.agent = None
        self.agent_name = None
        self.agent_instructions = None

    async def get_service_and_agent_config(self) -> ResolvedOrchestratorConfig:
        config = load_file(self.eval_config.config_file_path, "yaml")
        return ResolvedOrchestratorConfig(**config)
    
    async def create_kernel_from_config(self, config: ResolvedOrchestratorConfig) -> None:
        self.kernel = create_kernel(config=config)

    @abstractmethod
    async def create_agent_from_config(self, config: ResolvedOrchestratorConfig) -> None:
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
        return await get_benchmark_answers(
                agent=self.agent,
                agent_config=self.agent_config,
                agent_instructions=self.agent_instructions,
                benchmark_questions=benchmark_questions,
                azure_ai_client=self.azure_ai_client,
                kernel=self.kernel,
                run_dir_path=run_dir_path
            )
    
    async def run_local_evaluation(self, experiment_id: str, eval_data_path: str) -> str:
        '''
        Run local evaluation using agent-specific evaluators. If no agent evaluators are found, skip local evaluation.
        '''

        agent_evaluators = get_agent_evaluators(
            evaluators_config=self.eval_config.metric_config,
            azure_openai_endpoint=self.azure_openai_endpoint
        )

        if not agent_evaluators:
            self.logger.warning("No evaluators found specific to agents. Skipping local evaluation.")
            return

        self.logger.info(f"Running local evaluation with evaluators: {list(agent_evaluators.keys())}")
        response = evaluate(
            evaluation_name=f"{experiment_id}_local_eval",
            data=eval_data_path,
            evaluators=agent_evaluators,
            azure_ai_project={
                "subscription_id":self.azure_subscription_id,
                "project_name":self.azure_workspace_name,
                "resource_group_name":self.azure_resource_group
            }
        )
        return response.get("studio_url")

    async def evaluate(self):
        """
        Main evaluation workflow that orchestrates all evaluation steps.
        """
        
        try:
            # Load dataset
            benchmark_questions = await self.load_evaluation_dataset()

            resolved_config = await self.get_service_and_agent_config()
            await self.create_kernel_from_config(resolved_config)

            await self.create_agent_from_config(resolved_config)
            
            # Create experiment ID
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M%S")
            experiment_id = f"Agent-Eval_Agent_eq_{self.agent_name}_Start_eq_{current_time}"
            run_dir_path = f"{os.path.dirname(__file__)}/../results/{experiment_id}"
            os.makedirs(run_dir_path, exist_ok=True)
            
            # Run agent-specific evaluation
            benchmark_answers_save_path = await self.get_responses(benchmark_questions, run_dir_path)
            
            # Upload results
            try:
                benchmark_data_id, _= self.project_client.upload_file(benchmark_answers_save_path)
            except Exception as e:
                self.logger.error(f"Failed to upload file: {e}")
                return

            # Run local evaluation if configured for agent evaluators
            local_eval_results_url = await self.run_local_evaluation(experiment_id, benchmark_answers_save_path)

            # Run evaluation and get results URL
            results_url = await self.run_ai_foundry_evaluation(benchmark_data_id, experiment_id)

            if results_url:
                self.logger.info(f"\nEvaluation run complete. Use AI project URI for detailed metrics: {results_url}")
            if local_eval_results_url:
                self.logger.info(f"Local evaluation results available at: {local_eval_results_url}")

        finally:
            # Cleanup
            if self.project_client:
                self.project_client.close()
            if self.azure_ai_client:
                await self.azure_ai_client.close()

