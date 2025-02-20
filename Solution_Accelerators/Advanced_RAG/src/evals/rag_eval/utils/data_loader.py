import argparse
import csv
import json
import os

import pandas as pd
from azure.ai.ml import MLClient

from common.utilities.files import load_file

cache_dir_root = os.path.join(os.path.dirname(__file__), "..", "cached_datasets")

def _get_aml_data_path(config: argparse.Namespace, aml_client: MLClient, file_ext: str) -> str:
    """
    Helper to get or download AML data. Returns a local path.
    file_ext is something like ".json" or ".csv".
    """
    print("Authenticating to AML...")

    matching_assets = [a for a in aml_client.data.list() if a.name == config.aml_dataset]
    if not matching_assets:
        raise ValueError(f"No AML dataset found with name '{config.aml_dataset}'.")

    latest_version = matching_assets[0].latest_version
    data_asset_info = aml_client.data.get(name=config.aml_dataset, version=latest_version)

    # Example local cache path
    cache_dir = os.path.join(
        cache_dir_root,
        config.aml_dataset,
        latest_version
    )
    os.makedirs(cache_dir, exist_ok=True)

    # Our cached file
    cache_file_path = os.path.join(cache_dir, f"{config.aml_dataset}{file_ext}")

    if os.path.exists(cache_file_path) and not config.no_cache:
        print("Using cached file:", cache_file_path)
        return None, cache_file_path

    # Otherwise, use the remote path
    print("Using AML path:", data_asset_info.path)
    return data_asset_info.path, cache_file_path


def _save_to_cache(data, cache_file_path: str):
    """
    Saves data to a local file at cache_file_path (JSON or CSV).
    `data` can be:
      - A Pandas DataFrame (for CSV)
      - A Python list/dict (for JSON)
    """
    os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
    ext = os.path.splitext(cache_file_path)[1].lower()

    if ext == ".csv":
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a Pandas DataFrame for CSV caching.")
        data.to_csv(cache_file_path, index=False, quoting=csv.QUOTE_ALL)
        print(f"DataFrame cached at {cache_file_path}")

    elif ext == ".json":
        with open(cache_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"JSON data cached at {cache_file_path}")
    else:
        raise ValueError(f"Unsupported file extension for caching: {ext}")


def get_tone_eval_data(config: argparse.Namespace, aml_client: MLClient) -> list:
    """
    Load a list of dicts with 'fine_tuned_answer' and 'control_answer' fields.
    Example:
    [
      { "fine_tuned_answer": "some text", "control_answer": "some text" },
      { "fine_tuned_answer": "another text", "control_answer": "another text" }
    ]
    """
    if config.aml_dataset:
        aml_data_path, cache_file_path = _get_aml_data_path(config, aml_client, ".json")
        if aml_data_path:
            data = pd.read_json(aml_data_path, lines=True).to_dict(orient="records")
        else:
            data = load_file(cache_file_path, "json")
        if not os.path.exists(cache_file_path) or config.no_cache:
            _save_to_cache(data, cache_file_path)
    else:
        print("Reading local dataset for tone eval...")
        data = pd.read_json(config.local_dataset).to_dict(orient="records")

    # Validate structure
    if not isinstance(data, list):
        raise ValueError("Data must be a list of dictionaries.")
    for idx, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"Row {idx} is not a dict.")
        for key in ["fine_tuned_answer", "control_answer"]:
            if key not in row:
                raise ValueError(f"Row {idx} is missing '{key}'.")
    return data


def get_rephraser_questions(config: argparse.Namespace, aml_client: MLClient) -> list:
    """
    Load a list of lists, each containing a conversation history.
    Example:
    [
      [
        {"user": "Some user message"},
        {"assistant": "Some assistant message"}
      ],
      [
        {"user": "Another user message"},
        {"assistant": "Another assistant message"}
      ]
    ]
    """
    if config.aml_dataset:
        aml_data_path, cache_file_path = _get_aml_data_path(config, aml_client, ".json")
        if aml_data_path:
            data = pd.read_json(aml_data_path, lines=True)["messages"].tolist()
        else:
            data = load_file(cache_file_path, "json")
        if not os.path.exists(cache_file_path) or config.no_cache:
            _save_to_cache(data, cache_file_path)
    else:
        print("Reading local dataset for rephraser...")
        data = pd.read_json(config.local_dataset, lines=True)["messages"].tolist()

    if not isinstance(data, list):
        raise ValueError("Expected top-level to be a list of lists.")
    for idx, item in enumerate(data):
        if not isinstance(item, list):
            raise ValueError(f"Item at index {idx} is not a list.")
    return data


def get_benchmark_questions(config: argparse.Namespace, aml_client: MLClient) -> pd.DataFrame:
    """
    Load or download a CSV of questions. Possibly sample or filter afterwards.
    """
    if config.aml_dataset:
        benchmark_path, cache_file_path = _get_aml_data_path(config, aml_client, ".csv")
        if benchmark_path:
            df = pd.read_csv(benchmark_path)
        else:
            df = pd.read_csv(cache_file_path)
        if not os.path.exists(cache_file_path) or config.no_cache:
            _save_to_cache(df, cache_file_path)
    else:
        print("Reading local benchmark CSV...")
        dataset_file_path = os.path.join(os.path.dirname(__file__), "../results/", config.local_dataset)
        df = pd.read_csv(dataset_file_path)

    # Basic validation
    if len(df) > df["question"].nunique():
        raise ValueError("Some questions appear more than once.")

    # Rename columns if they exist
    rename_map = {"Questions": "question", "Answers": "ground_truth", "Page Number": "page"}
    for old_col, new_col in rename_map.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    # Sample if requested
    if config.sample_size:
        df = df.sample(config.sample_size)

    # Repeat questions if needed
    df = df.loc[df.index.repeat(config.question_repeats)].reset_index(drop=True)

    # Filter by difficulty if requested
    if config.difficulty:
        before_count = len(df)
        df = df[df["difficulty"].str.lower().isin(config.difficulty)]
        after_count = len(df)
        print(f"Filtered difficulty from {before_count} to {after_count} rows.")

    return df