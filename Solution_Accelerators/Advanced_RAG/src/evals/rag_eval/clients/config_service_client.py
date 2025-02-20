import argparse
import json
import os

import requests


class ConfigServiceClient(object):
    """
    A client for the config service. The config service is used to store and retrieve configs for the RAG Bot runtime.
    This allows users to have different configs for different experiments and to share configs between users.
    """

    def __init__(self, config_service_url):
        self.config_service_url = config_service_url
        if not self.is_healthy():
            raise ValueError("Config service is not healthy.")

    def is_healthy(self) -> bool:
        """
        Check if the config service is healthy.

        Returns:
            bool: True if the config service is healthy, False otherwise.
        """

        response = requests.get(f"{self.config_service_url}/configuration-service")
        return response.status_code == 200

    def is_remote_config_name(self, runtime_name: str, config_name: str) -> bool:
        """
        Check if the config path that the user provided is an existing remote config ID.

        Args:
            runtime_name (str): The runtime name. Likely either "orchestrator_runtime" or "search_runtime
            config_name (str): The config name.

        Returns:
            bool: True if the config path is a remote config ID, False otherwise.
        """

        url = f"{self.config_service_url}/configuration-service/configs/{runtime_name}/{config_name}"
        response = requests.get(url)
        is_remote_config = response.status_code != 404
        return is_remote_config

    def upload_config(self, runtime_name: str, config: argparse.Namespace) -> str:
        """
        Upload a config to the config service.

        Args:
            runtime_name (str): The runtime name. Likely either "orchestrator_runtime" or "search_runtime
            config (argparse.Namespace): The arguments class.

        Returns:
            str: The config name to include in the RAG Bot requests.
        """

        # check if the provided config is a remote config ID
        config_name = None
        if runtime_name == "orchestrator_runtime":
            config_name = config.orchestrator_config
        elif runtime_name == "search_runtime":
            config_name = config.search_config
        else:
            raise ValueError(f"Unsupported runtime name {runtime_name}")

        is_remote_config = self.is_remote_config_name(runtime_name, config_name)
        if is_remote_config:
            print(f"Config {config_name} is a remote config ID. Skipping upload.")
            return config_name

        if not os.path.exists(config_name):
            raise ValueError(f"Config file {config_name} does not exist locally.")

        config_json = json.load(open(config_name))
        if "config_version" in config_json:
            print(
                f"WARNING: The config file {config_name} already contains a 'config_version' field. This field will be overwritten with {config_name}."
            )

        config_json["config_version"] = config_name
        config_post_url = f"{self.config_service_url}/configuration-service/configs/{runtime_name}"
        response = requests.post(config_post_url, json=config_json)
        if response.status_code != 200:
            raise ValueError(f"Failed to upload config to the config service. Response: {response.text}")

        print(f"Uploaded {runtime_name} with version {config_name} to the config service.")
        return config_json["config_version"]

    def save_configs(self, config: argparse.Namespace):
        """
        Save the orchestrator and search configs to disk.

        Args:
            config (argparse.Namespace): The config object containing the orchestrator and search configs if they exist.
        """

        current_dir = os.path.dirname(os.path.abspath(__file__))
        experiment_directory = f"{current_dir}/results/{config.experiment_id}"
        os.makedirs(experiment_directory, exist_ok=True)

        if config.orchestrator_config:
            config_service_response = requests.get(
                f"{self.config_service_url}/configuration-service/configs/orchestrator_runtime/{config.orchestrator_config}"
            )
            if config_service_response.status_code != 200:
                raise ValueError(
                    f"Failed to retrieve orchestrator config {config.orchestrator_config} from the config service."
                )

            orchestrator_config = config_service_response.json()
            orchestrator_config_path = (
                f"{experiment_directory}/custom_orchestrator_config-{config.orchestrator_config}.json"
            )
            json.dump(orchestrator_config, open(orchestrator_config_path, "w"), indent=2)
            print(f"Saved custom orchestrator config to {orchestrator_config_path}")

        if config.search_config:
            config_service_response = requests.get(
                f"{self.config_service_url}/configuration-service/configs/search_runtime/{config.search_config}"
            )
            if config_service_response.status_code != 200:
                raise ValueError(f"Failed to retrieve search config {config.search_config} from the config service.")

            search_config = config_service_response.json()
            search_config_path = f"{experiment_directory}/custom_search_config-{config.search_config}.json"
            json.dump(search_config, open(search_config_path, "w"), indent=2)
            print(f"Saved custom search config to {search_config_path}")
