import argparse
import json
import os

import pandas as pd
from promptflow.azure import PFClient


def get_flow_id(pf_client: PFClient, flow_name: str, config: argparse.Namespace) -> str:
    """
    Get the flow ID from Prompt Flow.
    """
    flows = pf_client.flows.list()
    for flow_info in flows:
        if flow_info.display_name == flow_name:
            print(f"Flow {flow_name} successfully found in workspace {config.workspace}.")
            return flow_info.name
    raise Exception(
        f"Flow {flow_name} not found in workspace {config.workspace}. "
        "Ensure you're referencing a flow you've created."
    )

def calculate_metrics(
    config: argparse.Namespace,
    pf_client: PFClient,
    flow_id: str,
    benchmark_answers: pd.DataFrame,
    current_dir: str,
    eval_set_aml_path: str,
):
    """
    Classify the benchmark answers using the evaluation Prompt flow and save the results to disk.
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
        columns={old_col: old_col.split(".")[-1] for old_col in list(run_details.columns)},
        inplace=True
    )
    run_details.to_csv(
        f"{current_dir}/results/{config.experiment_id}/run_details.csv", index=False
    )
    print("=" * 120)
    print(f"Run details saved to {current_dir}/results/{config.experiment_id}/run_details.csv\n")
    print(run_details)

    benchmark_answers = pd.read_csv(f"{current_dir}/results/{config.experiment_id}/benchmark_answers.csv")
    new_columns = ["index", "question"] + [col for col in run_details.columns if col not in benchmark_answers.columns]

    # Index name from Prompt Flow results is "output.linenumber" and is unnamed in benchmark_answers
    run_details.index.rename("index", inplace=True)
    run_details.reset_index(inplace=True)
    benchmark_answers.index.rename("index", inplace=True)
    benchmark_answers.reset_index(inplace=True)

    trimmed_run_details = run_details[new_columns]
    trimmed_run_details["index"] = trimmed_run_details["index"].astype(int)
    benchmark_answers["index"] = benchmark_answers["index"].astype(int)

    full_results = benchmark_answers.merge(
        trimmed_run_details, on=["index", "question"], how="inner"
    )
    assert len(full_results) == len(benchmark_answers), (
        "Some questions were not classified by the Prompt Flow."
    )

    full_results.to_csv(
        f"{current_dir}/results/{config.experiment_id}/full_results_with_scores.csv", index=False
    )

    # Example grouping
    difficulty_performance = None
    if "difficulty" in full_results.columns:
        difficulty_performance = full_results.groupby("difficulty").mean("gpt_similarity").to_dict()["gpt_similarity"]

    benchmark_performance = None
    if "benchmark" in full_results.columns:
        benchmark_performance = full_results.groupby("benchmark").mean("gpt_similarity").to_dict()["gpt_similarity"]

    tags_performance = None
    if "tags" in full_results.columns:
        tags_performance = full_results.groupby("tags").mean("gpt_similarity").to_dict()["gpt_similarity"]

    machine_difficulty_performance = None
    if "machine_difficulty" in full_results.columns:
        machine_difficulty_performance = full_results.groupby("machine_difficulty").mean("gpt_similarity").to_dict()["gpt_similarity"]

    run_metrics = pf_client.get_metrics(base_run)
    combined_experiment_performance = {
        "overall_mean_similarity": run_metrics["gpt_similarity"],
        "by_machine_difficulty": machine_difficulty_performance,
        "by_difficulty": difficulty_performance,
        "by_tags": tags_performance,
        "by_source": benchmark_performance,
    }

    with open(f"{current_dir}/results/{config.experiment_id}/run_metrics.json", "w") as f:
        json.dump(combined_experiment_performance, f, indent=4)

    print("=" * 120)
    print(f"Metrics saved to {current_dir}/results/{config.experiment_id}/run_metrics.json\n")
    print(json.dumps(combined_experiment_performance, indent=4))
