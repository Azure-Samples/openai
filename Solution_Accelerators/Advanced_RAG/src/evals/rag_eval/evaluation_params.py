import argparse
import json
import os
import sys

import pandas as pd


def load_previous_run_config():
    """
    Load the configuration from the previous run to resume the evaluation.
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


def get_arguments():
    """
    Parse the command line arguments and set default values for the arguments that are not provided.
    """
    # Check if we are resuming from a previous run
    is_resume_run = any(["--resume_run_id" in arg for arg in sys.argv])
    if is_resume_run:
        return load_previous_run_config()

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    arg_parser.add_argument(
        "--eval_flow",
        type=str,
        required=True,
        help="Name of the evaluation flow to be executed.",
        choices=["evaluate_end_to_end", "evaluate_tone", "evaluate_fanout_rephraser"],
        default=None,
    )

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
        help="Name of the Prompt flow in AML to be used for evaluation.",
        default=None,
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
        default="https://ragbotdemoappdev.westus2.cloudapp.azure.com",
    )
    arg_parser.add_argument(
        "--config_address",
        type=str,
        required=False,
        help="The HTTP address of the Config service. Defaults to INT.",
        default="https://ragbotdemoappdev.westus2.cloudapp.azure.com",
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
    # if not parsed_config.aml_dataset and not parsed_config.local_dataset:
    #     raise Exception("Please provide one of --aml_dataset or --local_dataset.")

    # Normalize difficulty
    if parsed_config.difficulty:
        parsed_config.difficulty = [d.lower().strip() for d in parsed_config.difficulty.split(",")]

    # Create an experiment ID and persist the config
    current_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M%S")
    dataset_name = parsed_config.aml_dataset if parsed_config.aml_dataset else parsed_config.local_dataset.split(".")[0]
    experiment_id = f"RAG-Eval_Dataset_eq_{dataset_name}_Start_eq_{current_time}"
    parsed_config.experiment_id = experiment_id

    base_path = os.path.join(os.path.dirname(__file__), "results")
    save_path = os.path.normpath(os.path.join(base_path, experiment_id))
    if not save_path.startswith(base_path):
        raise Exception("Invalid experiment ID resulting in unsafe path")
    parsed_config.save_path = save_path
    os.makedirs(save_path, exist_ok=True)
    with open(os.path.join(save_path, "config.json"), "w") as f:
        json.dump(vars(parsed_config), f, indent=4)

    return parsed_config
