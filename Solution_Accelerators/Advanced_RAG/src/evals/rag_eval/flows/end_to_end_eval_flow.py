import argparse
import json
import os

import pandas as pd
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from clients.answer_client import get_benchmark_answers
from clients.config_service_client import ConfigServiceClient
from flows.flow import Flow
from metrics import calculate_metrics, get_flow_id
from promptflow.azure import PFClient
from utils.aml_utils import save_answers, upload_answers_to_aml
from utils.data_loader import get_benchmark_questions
from utils.debug_utils import get_mock_benchmark_answers


class EndToEndEvalFlow(Flow):
    def __init__(self, params: argparse.Namespace):
        super().__init__()
        self._params = params

    def evaluate(self):
        """
        Main function that orchestrates:
        1. Reading the evaluation dataset
        2. Getting RAG Bot answers
        3. Uploading results to AML
        4. Running PromptFlow to compute metrics
        5. Saving combined results
        """
        print("=" * 120)
        print("All directories, AML artifacts, and configurations will be tagged with the experiment ID.")
        print(f"Experiment ID: {self._params.experiment_id}")
        print("=" * 120)

        # print("Initializing Config Service client...")
        # config_service_client = ConfigServiceClient(self._params.config_address)

        # # Upload orchestrator/search configs if provided
        # self._params.orchestrator_config = (
        #     config_service_client.upload_config("orchestrator_runtime", self._params)
        #     if self._params.orchestrator_config
        #     else None
        # )
        # self._params.search_config = (
        #     config_service_client.upload_config("search_runtime", self._params) if self._params.search_config else None
        # )

        # if not self._params.orchestrator_config and not self._params.search_config:
        #     print("No configuration overrides provided. RAG Bot will use default configurations.")
        # else:
        #     config_service_client.save_configs(self._params)

        print("Authenticating to Prompt Flow...")
        azure_credential = DefaultAzureCredential()
        pf_client = PFClient(
            credential=azure_credential,
            subscription_id=self._params.subscription_id,
            resource_group_name=self._params.resource_group,
            workspace_name=self._params.workspace,
        )
        flow_id = get_flow_id(pf_client, self._params.aml_flow_name, self._params)

        aml_client = MLClient(
            azure_credential, self._params.subscription_id, self._params.resource_group, self._params.workspace
        )

        print("Getting benchmark questions...")
        benchmark_questions = get_benchmark_questions(self._params, aml_client)
        print(benchmark_questions.head())

        # Create local results directory
        run_dir_path = f"{os.path.dirname(__file__)}/../results/{self._params.experiment_id}"
        os.makedirs(run_dir_path, exist_ok=True)

        if self._params.debug_mock_rag_bot:
            print("Getting mock RAG Bot answers...")
            benchmark_answers = get_mock_benchmark_answers(benchmark_questions)
        else:
            print("Getting RAG Bot answers...")
            benchmark_answers = get_benchmark_answers(self._params, benchmark_questions)

        print(benchmark_answers.head())

        print("Saving RAG Bot answers to disk...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        answers_path = f"{current_dir}/results/{self._params.experiment_id}/benchmark_answers.csv"
        save_answers(self._params, current_dir, answers_path, benchmark_answers)

        print("Uploading RAG Bot answers to AML...")
        answers_aml_dataset_info = upload_answers_to_aml(self._params, aml_client, answers_path, benchmark_answers)

        print("Calculating metrics via Prompt Flow...")
        calculate_metrics(
            self._params, pf_client, flow_id, benchmark_answers, current_dir, answers_aml_dataset_info["aml_fs_path"]
        )

        # Combine everything for a final JSON
        combined_results_path = f"{current_dir}/results/{self._params.experiment_id}/combined_results.json"
        run_metrics_path = f"{current_dir}/results/{self._params.experiment_id}/run_metrics.json"
        run_details_path = f"{current_dir}/results/{self._params.experiment_id}/run_details.csv"

        combined_results = {
            "params": vars(self._params),
            "metrics": json.load(open(run_metrics_path)),
            "answers": pd.read_csv(run_details_path).to_dict(),
        }
        with open(combined_results_path, "w") as f:
            json.dump(combined_results, f, indent=4)

        return combined_results
