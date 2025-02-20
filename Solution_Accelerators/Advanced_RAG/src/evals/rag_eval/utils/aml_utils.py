import argparse
import csv
import json
import os

import pandas as pd
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data


def upload_answers_to_aml(
    config: argparse.Namespace,
    aml_client: MLClient,
    answers_path: str,
    benchmark_answers: pd.DataFrame,
) -> dict:
    """
    Upload the RAG Bot answers to AML. A new version is created for each upload attempt.
    """
    data_asset = Data()
    data_asset.name = config.experiment_id
    data_asset.description = (
        "This dataset stores RAG Bot's answers for evaluations. A new version is created "
        "for each evaluation run. See the tags for the configuration used for this evaluation."
    )
    data_asset.path = answers_path
    data_asset.type = AssetTypes.URI_FILE
    data_asset.tags = vars(config)
    data_asset.version = "1"

    upload_success = False
    while not upload_success:
        current_version = int(data_asset.version)
        if current_version > config.max_upload_attempts:
            raise Exception("Failed to upload data asset after exceeding max attempts.")

        try:
            # If the dataset version exists, increment and try again
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


def save_answers(config: argparse.Namespace, current_dir: str, answers_path: str, benchmark_answers: pd.DataFrame):
    """
    Write RAG Bot answers to disk. These results do not include the metrics from Prompt Flow.
    """
    os.makedirs(f"{current_dir}/results", exist_ok=True)
    os.makedirs(f"{current_dir}/results/{config.experiment_id}", exist_ok=True)

    benchmark_answers.to_csv(answers_path, index=False, quoting=csv.QUOTE_ALL)

    # Save the config for reference
    with open(f"{current_dir}/results/{config.experiment_id}/config.json", "w") as f:
        json.dump(vars(config), f, indent=4)

    print(f"Answers saved to {answers_path}")
