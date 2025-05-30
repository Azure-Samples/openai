# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import csv
import json
import os

import pandas as pd
from azure.ai.ml import MLClient

from common.utilities.files import load_file
from common.contracts.configuration.eval_config import EvaluationJobConfig

cache_dir_root = os.path.join(os.path.dirname(__file__), "..", "cached_datasets")

def _get_aml_data_path(config: EvaluationJobConfig, aml_client: MLClient, file_ext: str) -> str:
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

    if os.path.exists(cache_file_path) and config.use_cached_dataset:
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


def get_benchmark_questions(config: EvaluationJobConfig, aml_client: MLClient) -> pd.DataFrame:
    """
    Load or download a CSV of questions. Possibly sample or filter afterwards.
    """
    if config.aml_dataset:
        benchmark_path, cache_file_path = _get_aml_data_path(config, aml_client, ".csv")
        if benchmark_path:
            df = pd.read_csv(benchmark_path)
        else:
            df = pd.read_csv(cache_file_path)
        if not os.path.exists(cache_file_path) or not config.use_cached_dataset:
            _save_to_cache(df, cache_file_path)
    else:
        print("Reading local benchmark CSV...")
        df = pd.read_csv(config.local_dataset)

    # Basic validation
    if len(df) > df["question"].nunique():
        raise ValueError("Some questions appear more than once.")

    # Rename columns if they exist
    rename_map = {"question": "query", "answer": "ground_truth"}
    for old_col, new_col in rename_map.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    return df