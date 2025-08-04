# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import pandas as pd

from common.telemetry.app_logger import AppLogger
from common.contracts.configuration.eval_config import EvaluationJobConfig
from evals.eval_types.eval_base import EvalBase
from evals.clients.answer_client import get_benchmark_answers

class EndToEndEvalBase(EvalBase):
    """
    Base class for end to end evaluation.
    """
    def __init__(
            self,
            eval_config: EvaluationJobConfig,
            ai_project_conn_str: str, 
            azure_openai_endpoint: str,
            azure_subscription_id: str, 
            azure_resource_group: str, 
            azure_workspace_name: str,
            logger: AppLogger,
            session_manager_uri: str,
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
        self.session_manager_uri = session_manager_uri

    async def get_responses(self, benchmark_questions: pd.DataFrame, run_dir_path: str) -> pd.DataFrame:
        """
        Get responses from session manager endpoint for the provided benchmark questions.

        Args:
            benchmark_questions: DataFrame containing the evaluation dataset
            run_dir_path: Path to the directory for saving evaluation results

        Returns:
            DataFrame containing responses
        """
        return await get_benchmark_answers(
                benchmark_questions=benchmark_questions,
                session_manager_uri=self.session_manager_uri,
                run_dir_path=run_dir_path
            )

    async def evaluate(self):
        """
        Main evaluation workflow that orchestrates all evaluation steps.
        """
        
        try:
            # Load dataset
            benchmark_questions = await self.load_evaluation_dataset()
            
            # Create experiment ID
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M%S")
            experiment_id = f"End_to_End_Eval_Dataset_eq_{self.eval_config.aml_dataset}_Start_eq_{current_time}"
            run_dir_path = f"{os.path.dirname(__file__)}/../results/{experiment_id}"
            os.makedirs(run_dir_path, exist_ok=True)
            
            # Get responses from session manager
            benchmark_answers_save_path = await self.get_responses(benchmark_questions, run_dir_path)
            
            # Upload results
            benchmark_data_id, _= self.project_client.upload_file(benchmark_answers_save_path)

            # Run evaluation and get results URL
            results_url = await self.run_ai_foundry_evaluation(benchmark_data_id, experiment_id)
            
            self.logger.info(f"\nEvaluation run complete. Use AI project URI for detailed metrics: {results_url}")

        finally:
            # Cleanup
            if self.project_client:
                self.project_client.close()

