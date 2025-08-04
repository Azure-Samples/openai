# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from abc import ABC, abstractmethod
from typing import Dict
import time
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from azure.ai.projects.models import Evaluation, EvaluatorConfiguration, InputDataset
from azure.ai.projects.aio import AIProjectClient

from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import EvaluationJobConfig

from common.evals.utils.data_loader import get_benchmark_questions
from common.evals.utils.evaluator_utils import get_evaluators


class EvalBase(ABC):
    def __init__(
        self,
        eval_config: EvaluationJobConfig,
        azure_openai_endpoint: str,
        azure_subscription_id: str,
        azure_resource_group: str,
        azure_workspace_name: str,
        logger: AppLogger,
        ai_project_endpoint: str,
        azure_openai_api_key: str,
    ):
        self.eval_config: EvaluationJobConfig = eval_config
        self.ai_project_endpoint = ai_project_endpoint
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_subscription_id = azure_subscription_id
        self.azure_resource_group = azure_resource_group
        self.azure_workspace_name = azure_workspace_name
        self.logger = logger
        self.azure_openai_api_key = azure_openai_api_key

        # Use the factory to create the client with backwards compatibility
        self.project_client = AIProjectClient(
            endpoint=self.ai_project_endpoint,
            credential=DefaultAzureCredential(),
        )

    async def load_evaluation_dataset(self) -> pd.DataFrame:
        """Load and return the evaluation dataset."""
        aml_client = MLClient(
            credential=DefaultAzureCredential(),
            subscription_id=self.azure_subscription_id,
            resource_group_name=self.azure_resource_group,
            workspace_name=self.azure_workspace_name,
        )

        self.logger.info("Getting benchmark questions...")
        benchmark_questions = get_benchmark_questions(config=self.eval_config, aml_client=aml_client)
        self.logger.info(f"Loaded benchmark questions: {benchmark_questions.head()}")
        return benchmark_questions

    @abstractmethod
    async def get_responses(self, benchmark_questions: pd.DataFrame, run_dir_path: str) -> pd.DataFrame:
        """
        This method should be implemented by subclasses.
        """
        pass

    def create_evaluators(self) -> Dict[str, EvaluatorConfiguration]:
        """Create and return evaluator instances based on metric configuration."""
        return get_evaluators(
            evaluators_config=self.eval_config.metric_config,
        )

    async def run_ai_foundry_evaluation(self, benchmark_data_id: str, experiment_id: str) -> str:
        """Execute evaluation in AI Foundry and return results URL."""
        evaluators = self.create_evaluators()
        if not evaluators:
            self.logger.warning("No evaluators found for cloud evaluation. Skipping cloud evaluation.")
            return

        data = InputDataset(id=benchmark_data_id)
        evaluation = Evaluation(display_name=experiment_id, data=data, evaluators=evaluators)

        evaluation_response: Evaluation = await self.project_client.evaluations.create(
            evaluation=evaluation,
            headers={
                "model-endpoint": self.azure_openai_endpoint,
                "api-key": self.azure_openai_api_key,
            },
        )

        # Poll evaluation status
        start_time = time.monotonic()
        eval_timeout = start_time + 60 * 10  # 10 Minutes

        while True:
            try:
                evaluation: Evaluation = await self.project_client.evaluations.get(evaluation_response.name)

                if evaluation.status == "Completed":
                    self.logger.info(f"Evaluation {evaluation.name} completed successfully!")
                    break
                else:
                    self.logger.info(f"Evaluation {evaluation.name} is {evaluation.status}..")

                if time.monotonic() > eval_timeout:
                    self.logger.warning(f"Evaluation {evaluation.name} timed out.")
                    break

                time.sleep(5)
            except Exception as ex:
                self.logger.error(f"Error checking evaluation status. Evaluation {evaluation.name}. Error: {ex}")
                break

        end_time = (time.monotonic() - start_time) / 60
        self.logger.info(f"Evaluation run complete. Total duration: {end_time} minutes.")

        return evaluation_response.properties["AiStudioEvaluationUri"]

    @abstractmethod
    async def evaluate(self):
        """
        Execute specific evaluation
        """
        pass
