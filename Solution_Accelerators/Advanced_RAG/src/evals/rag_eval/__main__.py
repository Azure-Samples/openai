"""
TODO: Remove this file after testing unified eval. 
"""

import argparse
import csv
import json
import os
import sys
import time
import uuid

import pandas as pd
import requests
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data
from azure.identity import DefaultAzureCredential
from clients.config_service_client import ConfigServiceClient
from promptflow.azure import PFClient
from tqdm import tqdm
from utils.debug_utils import get_mock_benchmark_answers

from common.contracts.common.user_prompt import (
    PayloadType,
    UserPrompt,
    UserPromptPayload,
)
from common.contracts.session_manager.chat_request import ChatRequest


def get_arguments():
    """
    Parse the command line arguments and set default values for the arguments that are not provided.

    Returns:
        argparse.Namespace: The parsed arguments provided by the user and the default values for the arguments that are not provided.
    """
    is_resume_run = any(["--resume_run_id" in arg for arg in sys.argv])
    if is_resume_run:
        return load_previous_run_config()

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument(
        "--aml_dataset",
        type=str,
        required=False,
        help="Name of the evaluation dataset in AML. See README for common options. Can't be used with --local_dataset.",
        default=None,
    )
    arg_parser.add_argument(
        "--local_dataset",
        type=str,
        required=False,
        help="The path to the local evaluation dataset. Can't be used with --aml_dataset.",
        default=None,
    )
    arg_parser.add_argument(
        "--difficulty",
        type=str,
        required=False,
        help="The difficulty of the questions in the evaluation dataset. Defaults to running all difficulties.",
        default=None,
    )
    arg_parser.add_argument(
        "--no_cache",
        action="store_true",
        help="Do not use the cached version of the evaluation dataset.",
    )
    arg_parser.add_argument(
        "--question_repeats",
        type=int,
        required=False,
        help="The number of times to repeat each question in the evaluation dataset. Defaults to 1.",
        default=1,
    )
    arg_parser.add_argument(
        "--aml_flow_name",
        type=str,
        required=False,
        help="Name of the Prompt flow in AML",
        default="RAG_E2E_Eval_Flow",
    )
    arg_parser.add_argument("--subscription_id", type=str, required=True, help="Azure subscription ID")
    arg_parser.add_argument(
        "--resource_group",
        type=str,
        required=False,
        help="Azure resource group",
        default="RAGBotDemo",
    )
    arg_parser.add_argument(
        "--workspace",
        type=str,
        required=False,
        help="Azure workspace",
        default="RAGBotDemo_AML_WS",
    )
    arg_parser.add_argument(
        "--orchestrator_config",
        type=str,
        required=False,
        help="The absolute path to the orchestrator configuration file which will be posted to the Config service or the ID for an existing config",
        default=None,
    )
    arg_parser.add_argument(
        "--search_config",
        type=str,
        required=False,
        help="The absolute path to the search configuration file which will be posted to the Config service or the ID for an existing config",
        default=None,
    )
    arg_parser.add_argument(
        "--conversation_id_prefix",
        type=str,
        required=False,
        help="Conversation ID prefix to use if any.",
        default=None,
    )
    arg_parser.add_argument(
        "--search_topk",
        type=int,
        required=False,
        help="The number of search results to return.",
        default=200,
    )
    arg_parser.add_argument(
        "--address",
        type=str,
        required=False,
        help="The HTTP address of the RAG Bot service. Defaults to INT.",
        default="https://ragbot.westus2.cloudapp.azure.com",
    )
    arg_parser.add_argument(
        "--config_address",
        type=str,
        required=False,
        help="The HTTP address of the Config service. Defaults to INT.",
        default="https://ragbot.westus2.cloudapp.azure.com",
    )
    arg_parser.add_argument(
        "--max_upload_attempts",
        type=int,
        required=False,
        help="The maximum number of attempts to upload the results to AML. Defaults to 10000.",
        default=10000,
    )
    arg_parser.add_argument(
        "--sample_size",
        type=int,
        required=False,
        help="The number of samples to evaluate. Defaults to 10.",
        default=None,
    )
    arg_parser.add_argument(
        "--debug_mock_rag_bot",
        action="store_true",
        help="Make up RAG Bot responses by using an LM to paraphrase the ground-truth answer.",
    )
    arg_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose logs.",
    )

    parsed_config = arg_parser.parse_args()
    if parsed_config.aml_dataset and parsed_config.local_dataset:
        raise Exception("Please provide only one of --aml_dataset or --local_dataset.")
    if not parsed_config.aml_dataset and not parsed_config.local_dataset:
        raise Exception("Please provide one of --aml_dataset or --local_dataset.")
    if parsed_config.difficulty:
        parsed_config.difficulty = [difficulty.lower() for difficulty in parsed_config.difficulty.split(",")]

    current_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M%S")
    aml_dataset = parsed_config.aml_dataset
    experiment_id = f"RAG-Bot-Eval_Dataset_eq_{aml_dataset}_Start_eq_{current_time}"
    parsed_config.experiment_id = experiment_id

    save_path = os.path.join(os.path.dirname(__file__), f"results/{experiment_id}")
    os.makedirs(save_path, exist_ok=True)
    with open(f"{save_path}/config.json", "w") as f:
        json.dump(vars(parsed_config), f, indent=4)

    return parsed_config


def load_previous_run_config():
    """
    Load the configuration from the previous run to resume the evaluation.

    Returns:
        argparse.Namespace: The parsed arguments provided by the user and the default values for the arguments that are not provided
    """
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument(
        "--resume_run_id",
        type=str,
        required=False,
        help="The experiment ID of the previous run to resume. The configuration will be loaded from the previous run and the RAG Bot answer component will continue from where it left off.",
        default=None,
    )
    parsed_config = arg_parser.parse_args()
    config_path = f"{os.path.dirname(__file__)}/results/{parsed_config.resume_run_id}/config.json"
    parsed_config = json.load(open(config_path, "r"))

    print(f"Resuming run with ID: {parsed_config['experiment_id']}")
    print(f"Config: {json.dumps(parsed_config, indent=4)}")
    return argparse.Namespace(**parsed_config)


def get_benchmark_questions(config: argparse.Namespace, aml_client: MLClient) -> pd.DataFrame:
    """
    Download the benchmark questions from AML.

    Args:
        config (argparse.Namespace): User-provided and default configuration.
        aml_client (MLClient): The Azure ML client.

    Returns:
        pd.DataFrame: The benchmark questions.
    """
    benchmark_data = None
    if config.aml_dataset:
        print("Authenticating to AML...")
        latest_dataset_version = [asset for asset in aml_client.data.list() if asset.name == config.aml_dataset][
            0
        ].latest_version
        data_asset_info = aml_client.data.get(name=config.aml_dataset, version=latest_dataset_version)
        benchmark_path = data_asset_info.path

        cache_dataset_path = f"{os.path.dirname(__file__)}/cached_datasets/{config.aml_dataset}"
        cache_file_path = f"{cache_dataset_path}/{latest_dataset_version}/{config.aml_dataset}.csv"
        if os.path.exists(cache_file_path) and not config.no_cache:
            print("Reading the cached evaluation dataset...")
            benchmark_path = cache_file_path
        elif os.path.exists(cache_file_path):
            print(
                "A local cache exists, but the --no_cache flag is set. Downloading the evaluation dataset from AML..."
            )
        elif os.path.exists(cache_dataset_path):
            print("A new dataset version is available. Pulling data from AML...")
        else:
            print("No cached version found locally. Downloading the evaluation dataset from AML...")

        benchmark_data = pd.read_csv(benchmark_path)

        should_save_cache = not os.path.exists(cache_file_path) and not config.no_cache
        if should_save_cache:
            os.makedirs(
                f"{os.path.dirname(__file__)}/cached_datasets/{config.aml_dataset}/{latest_dataset_version}",
                exist_ok=True,
            )
            benchmark_data.to_csv(cache_file_path, index=False, quoting=csv.QUOTE_ALL)
            print(f"Dataset saved to {cache_file_path}")

    else:
        print("Reading the local evaluation dataset...")
        benchmark_data = pd.read_csv(config.local_dataset)

    if len(benchmark_data) > benchmark_data["question"].nunique():
        raise Exception("there are rows with the same question")

    columns_to_rename = {
        "Questions": "question",
        "Answers": "ground_truth",
        "Page Number": "page",
    }
    for col_name in columns_to_rename:
        if col_name in benchmark_data.columns:
            benchmark_data.rename(columns={col_name: columns_to_rename[col_name]}, inplace=True)

    if config.sample_size:
        print(f"Sampling {config.sample_size} questions from the benchmark data.")
        benchmark_data = benchmark_data.sample(config.sample_size)

    benchmark_data = benchmark_data.loc[benchmark_data.index.repeat(config.question_repeats)].reset_index(drop=True)

    if config.question_repeats > 1:
        print(
            f"Repeating each question {config.question_repeats} times. The benchmark data now has {len(benchmark_data)} questions."
        )

    benchmark_data = benchmark_data.reset_index()
    if config.difficulty:
        before_count = len(benchmark_data)
        benchmark_data = benchmark_data[
            benchmark_data["difficulty"].apply(lambda row_difficulty: row_difficulty.lower() in config.difficulty)
        ]
        after_count = len(benchmark_data)
        print(
            f"Filtered by difficulty: {config.difficulty}. Number of questions before filtering: {before_count}. Number of questions after filtering: {after_count}"
        )

    return benchmark_data


def log_response_info(
    request_body: dict, response_json: dict, response: requests.Response, config: argparse.Namespace
):
    """
    Log the request and response information.

    Args:
        request_body (dict): The request body.
        response_json (dict): The response JSON.
        response (requests.Response): The response object.
        config (argparse.Namespace): User-provided and default configuration.
    """
    http_info = {
        "request_body": request_body,
        "response": response_json,
        "status_code": response.status_code,
    }
    requests_logs_path = f"{os.path.dirname(__file__)}/results/{config.experiment_id}/requests_logs.json"
    requests_logs = {"logs": []}
    if os.path.exists(requests_logs_path):
        requests_logs = json.load(open(requests_logs_path))

    requests_logs["logs"].append(http_info)
    json.dump(requests_logs, open(requests_logs_path, "w"), indent=4)


def get_answer(row: pd.Series, config: argparse.Namespace, requests_session: requests.Session) -> pd.DataFrame:
    """
    Get the answer from RAG Bot.

    Args:
        row (pd.Series): The row of the benchmark questions.
        config (argparse.Namespace): User-provided and default configuration.
        requests_session (requests.Session): The requests session.

    Returns:
        pd.DataFrame: The benchmark row with RAG Bot's answer.
    """
    if config.conversation_id_prefix:
        conversation_id = f"{config.conversation_id_prefix}_{uuid.uuid4().hex[:6]}"
    else:
        conversation_id = f"{config.experiment_id}_{uuid.uuid4().hex[:6]}"

    request_body = {
        "user_id": "anonymous",
        "conversation_id": conversation_id,
        "dialog_id": uuid.uuid4().hex,
        "dialog": row["question"],
        "overrides": {},
    }

    chat_request = ChatRequest(
        conversation_id=conversation_id,
        user_id=uuid.uuid4().hex,
        dialog_id=uuid.uuid4().hex,
        message=UserPrompt(UserPromptPayload(type=PayloadType.TEXT, value=row["question"])),
    )

    if config.orchestrator_config:
        chat_request.overrides.orchestrator_runtime.config_version = config.orchestrator_config

    if config.search_config:
        chat_request.overrides.search_overrides = config.search_config

    if config.search_topk:
        parsed_search_topk = int(config.search_topk)
        if "search_overrides" not in request_body["overrides"]:
            chat_request.overrides.search_overrides = None

        chat_request.overrides.search_overrides.top = parsed_search_topk

    print(f"\nSending request: {chat_request.model_dump_json()}")
    response = requests_session.post(f"{config.address}/chat", json=chat_request.model_dump_json())
    if response.status_code != 200:
        error = (
            f"Failed to get answer. CODE={response.status_code}, RESPONSE={response.text}, QUESTION={row['question']}"
        )
        raise Exception(error)

    response_json = response.json()
    if response_json.get("error"):
        error = f"Failed to get answer. RESPONSE={response_json}, QUESTION={row['question']}"
        raise Exception(error)

    search_queries = []
    cognitive_search_skill_info = response_json["answer"]["steps_execution"]["cognitiveSearchSkill"]
    for query_info in cognitive_search_skill_info["step_input"]["search_queries"]:
        search_queries.append(query_info["search_query"])

    document_scores = []
    for search_results in cognitive_search_skill_info["step_output"]["results"]:
        current_result_scores = []
        for document_info in search_results["search_results"]:
            try:
                score_col_name = (
                    "@search.reranker_score" if "@search.reranker_score" in document_info else "search_score"
                )
                current_result_scores.append(document_info[score_col_name])
            except Exception as error:
                current_result_scores.append(0)
                if config.verbose:
                    print(f"Failed to get score for document: {document_info}. Setting score to 0. Error: {error}")

        document_scores.append(current_result_scores)

    if config.verbose:
        log_response_info(request_body, response_json, response, config)
        print("\n" + "-" * 120)
        print(f"QUESTION: {row['question']}")
        print(f"ANSWER: {response_json['answer']['answer_string']}")
        print("\n" + "-" * 120)

    answer_frame_row = row.to_dict()
    answer_frame_row["search_queries"] = search_queries
    answer_frame_row["context_score"] = document_scores
    answer_frame_row["contexts"] = response_json["data_points"]
    answer_frame_row["answer"] = response_json["answer"]["answer_string"]
    answer_frame_row["cached_answer"] = False
    answer_frame = pd.DataFrame([answer_frame_row])
    return answer_frame


def get_benchmark_answers(config: argparse.Namespace, benchmark_questions: pd.DataFrame) -> pd.DataFrame:
    """
    Get the benchmark answers from RAG Bot.

    Args:
        config (argparse.Namespace): User-provided and default configuration.
        benchmark_questions (pd.DataFrame): The benchmark questions.

    Returns:
        pd.DataFrame: The benchmark answers.
    """
    requests_session = requests.Session()
    benchmark_answers_save_path = f"{os.path.dirname(__file__)}/results/{config.experiment_id}/benchmark_answers.csv"
    answers_frame = pd.read_csv(benchmark_answers_save_path) if os.path.exists(benchmark_answers_save_path) else None
    if answers_frame is not None:
        print(f"Resuming from previous run. Loaded {len(answers_frame)} answers.")

    for index, row in tqdm(benchmark_questions.iterrows(), total=len(benchmark_questions), desc="Getting answers..."):
        if answers_frame is not None:
            answers_frame.to_csv(benchmark_answers_save_path, index=False, quoting=csv.QUOTE_ALL)

        is_answered_previosuly = (
            len(answers_frame) > index and answers_frame.iloc[index]["question"] == row["question"]
            if answers_frame is not None
            else False
        )
        if is_answered_previosuly:
            continue

        awaiting_rag_bot_answer = True
        while awaiting_rag_bot_answer:
            try:
                current_answer_frame = get_answer(row, config, requests_session)
                if answers_frame is None:
                    answers_frame = current_answer_frame
                else:
                    answers_frame = pd.concat([answers_frame, current_answer_frame], ignore_index=True)

                awaiting_rag_bot_answer = False
            except Exception as error:
                print(f"Failed to get answer for question: {row['question']}. Error: {error}")
                print("Retrying in 30 seconds...")
                time.sleep(30)

    return answers_frame


def upload_answers_to_aml(
    config: argparse.Namespace, aml_client: MLClient, answers_path: str, benchmark_answers: pd.DataFrame
) -> dict:
    """
    Upload the RAG Bot answers to AML. A new version is created for each upload attempt. The uploaded dataset is tagged with
    the configuration used for the evaluation.

    Args:
        config (argparse.Namespace): User-provided and default configuration.
        aml_client (MLClient): The Azure ML client.
        answers_path (str): The path to save the answers.
        benchmark_answers (pd.DataFrame): RAG Bot answers to the benchmark questions.

    Returns:
        dict: The information about the uploaded dataset
    """
    data_asset = Data()
    data_asset.name = config.experiment_id
    data_asset.description = """
    "This dataset stores RAG Bot's answers for evaluations. It is created by the RAG Bot eval tool, with a new version for
    each evaluation run. See the tags for the configuration used for this evaluation."""
    data_asset.path = answers_path
    data_asset.type = AssetTypes.URI_FILE
    data_asset.tags = vars(config)
    data_asset.version = "1"

    upload_success = False
    while not upload_success:
        current_version = int(data_asset.version)
        if current_version > config.max_upload_attempts:
            raise Exception("Failed to upload data asset after 500 attempts.")

        try:
            aml_client.data.get(name=config.experiment_id, version=str(current_version))
            data_asset.version = str(current_version + 1)
        except Exception:
            my_data = aml_client.data.create_or_update(data_asset)
            print(f"Data asset created. Name: {my_data.name}, version: {my_data.version}")
            upload_success = True

            return {
                "name": my_data.name,
                "version": my_data._version,
                "aml_fs_path": my_data._path,
                "id": my_data._id,
            }


def save_answers(current_dir: str, answers_path: str, benchmark_answers: pd.DataFrame):
    """
    Write RAG Bot answers to disk. These results do not include the metrics calculated by Prompt flow.

    Args:
        current_dir (str): The current file directory.
        answers_path (str): The path to save the answers.
        benchmark_answers (pd.DataFrame): RAG Bot answers to the benchmark questions.
    """
    os.makedirs(f"{current_dir}/results", exist_ok=True)
    os.makedirs(f"{current_dir}/results/{config.experiment_id}", exist_ok=True)
    benchmark_answers.to_csv(answers_path, index=False, quoting=csv.QUOTE_ALL)
    json.dump(vars(config), open(f"{current_dir}/results/{config.experiment_id}/config.json", "w"), indent=4)
    print(f"Answers saved to {answers_path}")


def calculate_metrics(
    config: argparse.Namespace,
    pf_client: PFClient,
    flow_id: str,
    benchmark_answers: pd.DataFrame,
    current_dir: str,
    eval_set_aml_path: str,
):
    """
    Classify the benchmark answers using the RAG Bot evaluation Prompt flow and save the results to disk.

    Args:
        config (argparse.Namespace): User-provided and default configuration.
        pf_client (PFClient): The Prompt Flow client.
        flow_id (str): The ID of the Prompt flow.
        benchmark_answers (pd.DataFrame): RAG Bot answers to the benchmark questions.
        current_dir (str): The current file directory.
        eval_set_aml_path (str): The path to the evaluation dataset in AML.
    """

    print("Invoking Prompt Flow. This may take a few minutes. Check AML for progress.")
    column_mapping = {property: f"${{data.{property}}}" for property in benchmark_answers.columns}
    base_run = pf_client.run(
        flow=f"azureml:{flow_id}",
        data=eval_set_aml_path,
        name=config.experiment_id,
        tags=vars(config),
        column_mapping=column_mapping,
    )
    pf_client.stream(base_run)
    run_details = pf_client.get_details(base_run, all_results=True)
    run_details.rename(
        columns={old_col: old_col.split(".")[-1] for old_col in list(run_details.columns)}, inplace=True
    )
    run_details.to_csv(f"{current_dir}/results/{config.experiment_id}/run_details.csv", index=False)
    print("=" * 120)
    print(f"Run details saved to {current_dir}/results/{config.experiment_id}/run_details.csv\n")
    print(run_details)

    benchmark_answers = pd.read_csv(f"{current_dir}/results/{config.experiment_id}/benchmark_answers.csv")

    new_columns = ["index", "question"] + [col for col in run_details.columns if col not in benchmark_answers.columns]

    trimmed_run_details = run_details[new_columns]
    trimmed_run_details = trimmed_run_details.reset_index(drop=True)
    trimmed_run_details["index"] = trimmed_run_details["index"].astype(int)
    benchmark_answers["index"] = benchmark_answers["index"].astype(int)
    full_results = benchmark_answers.merge(trimmed_run_details, on=["index", "question"], how="inner")

    assert len(full_results) == len(benchmark_answers), "Some questions were not classified by the Prompt Flow."

    full_results.to_csv(f"{current_dir}/results/{config.experiment_id}/full_results_with_scores.csv", index=False)

    difficulty_performance = None
    if "difficulty" in full_results.columns:
        difficulty_performance = full_results.groupby("difficulty").mean("gpt_similarity").to_dict()["gpt_similarity"]
    else:
        print("No difficulty column found in the benchmark answers.")

    benchmark_performance = None
    if "benchmark" in full_results.columns:
        benchmark_performance = full_results.groupby("benchmark").mean("gpt_similarity").to_dict()["gpt_similarity"]
    else:
        print("No benchmark column found in the benchmark answers.")

    tags_performance = None
    if "tags" in full_results.columns:
        tags_performance = full_results.groupby("tags").mean("gpt_similarity").to_dict()["gpt_similarity"]
    else:
        print("No tags column found in the benchmark answers.")

    machine_difficulty_performance = None
    if "machine_difficulty" in full_results.columns:
        machine_difficulty_performance = (
            full_results.groupby("machine_difficulty").mean("gpt_similarity").to_dict()["gpt_similarity"]
        )

    run_metrics = pf_client.get_metrics(base_run)
    combined_experiment_performance = {
        "overall_mean_similarity": run_metrics["gpt_similarity"],
        "by_machine_difficulty": machine_difficulty_performance,
        "by_difficulty": difficulty_performance,
        "by_tags": tags_performance,
        "by_source": benchmark_performance,
    }
    json.dump(
        combined_experiment_performance,
        open(f"{current_dir}/results/{config.experiment_id}/run_metrics.json", "w"),
        indent=4,
    )

    print("=" * 120)
    print(f"Metrics saved to {current_dir}/results/{config.experiment_id}/combined_experiment_performance.json\n")
    print(json.dumps(combined_experiment_performance, indent=4))


def get_flow_id(pf_client: PFClient, flow_name: str) -> str:
    """
    Get the flow ID from Prompt Flow.

    Args:
        pf_client (PFClient): The Prompt Flow client.
        flow_name (str): The name of the flow.

    Returns:
        str: The flow ID.
    """
    for flow_info in pf_client.flows.list():
        if flow_info.display_name == flow_name:
            print(f"Flow {flow_name} successfully found in the workspace {config.workspace}.")
            return flow_info.name

    raise Exception(
        f"Flow {config.aml_flow_name} not found in the workspace {config.workspace}. Ensure you're referencing a flow you've created."
    )


def evaluate(config: argparse.Namespace):
    """Main function that reads the evaluation dataset from AML, calls RAG Bot, uploads results to AML, and logs.

    Args:
        config (argparse.Namespace): The user-provided and default configuration.
    """
    print("=" * 120)
    print("All directories, AML artifacts, and configurations will be tagged with the experiment ID.")
    print(f"Experiment ID: {config.experiment_id}")
    print("=" * 120)

    print("Initializing Config Service client...")
    config_service_client = ConfigServiceClient(config.config_address)

    config.orchestrator_config = (
        config_service_client.upload_config("orchestrator_runtime", config) if config.orchestrator_config else None
    )
    config.search_config = (
        config_service_client.upload_config("search_runtime", config) if config.search_config else None
    )
    if not config.orchestrator_config and not config.search_config:
        print("No configuration overrides provided. RAG Bot will use the default configurations.")
    if config.orchestrator_config or config.search_config:
        config_service_client.save_configs(config)

    print("Authenticating to Prompt Flow...")
    azure_credential = DefaultAzureCredential()
    pf_client = PFClient(
        credential=azure_credential,
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group,
        workspace_name=config.workspace,
    )
    flow_id = get_flow_id(pf_client, config.aml_flow_name)
    aml_client = MLClient(azure_credential, config.subscription_id, config.resource_group, config.workspace)

    print("Getting benchmark questions...")
    benchmark_questions = get_benchmark_questions(config, aml_client)
    print(benchmark_questions.head())

    # Ceate local results directory
    run_dir_path = f"{os.path.dirname(__file__)}/results/{config.experiment_id}"
    if not os.path.exists(run_dir_path):
        os.makedirs(run_dir_path)

    if config.debug_mock_rag_bot:
        print("Getting mock RAG Bot answers...")
        benchmark_answers = get_mock_benchmark_answers(benchmark_questions)
        print(benchmark_answers.head())
    else:
        print("Getting RAG Bot answers...")
        benchmark_answers = get_benchmark_answers(config, benchmark_questions)
        print(benchmark_answers.head())

    print("Saving RAG Bot answers to disk...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    answers_path = f"{current_dir}/results/{config.experiment_id}/benchmark_answers.csv"
    save_answers(current_dir, answers_path, benchmark_answers)

    print("Uploading RAG Bot answers to AML...")
    answers_aml_dataset_info = upload_answers_to_aml(config, aml_client, answers_path, benchmark_answers)

    print("Calculating metrics...")
    calculate_metrics(
        config, pf_client, flow_id, benchmark_answers, current_dir, answers_aml_dataset_info["aml_fs_path"]
    )

    combined_results = {
        "config": config.__dict__,
        "metrics": json.load(open(f"{current_dir}/results/{config.experiment_id}/run_metrics.json")),
        "answers": pd.read_csv(f"{current_dir}/results/{config.experiment_id}/run_details.csv").to_dict(),
    }
    json.dump(
        combined_results, open(f"{current_dir}/results/{config.experiment_id}/combined_results.json", "w"), indent=4
    )
    return combined_results


if __name__ == "__main__":
    print("RAG Eval")
    config = get_arguments()
    evaluate(config)
    print("=" * 120)
    print("Done!")
