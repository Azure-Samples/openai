# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import argparse
import requests

from common.utilities.files import load_file
from common.contracts.configuration.eval_config import EvaluationJobConfig
from common.contracts.configuration.config_type import ConfigType
from common.clients.services.config_service_client import ConfigServiceClient


async def get_preset_config(requested_config_type: str, config: EvaluationJobConfig, config_service_client:ConfigServiceClient):
    """
    Get the preset configuration based on the requested config type and the provided config.

    Args:
        requested_config_type (str): The type of configuration requested (e.g., "service" or "agent").
        eval_params (EvaluationJobConfig): The parameters provided by the user.
    """
    if config.config_file_path:
        return get_preset_config_from_file(requested_config_type, config)
    else:
        return await get_preset_config_from_endpoint(requested_config_type, config, config_service_client)


async def get_preset_config_from_endpoint(requested_config_type: str, eval_params: EvaluationJobConfig, config_service_client:ConfigServiceClient):
    """
    Get the preset configuration from a remote endpoint.

    Args:
        requested_config_type (str): The type of configuration requested (e.g., "service" or "agent").
        eval_params (EvaluationJobConfig): The parameters provided by the user.
        config_endpoint (str): The endpoint to fetch the configuration from.

    Returns:
        dict: The preset configuration as a dictionary.
    """
    if requested_config_type == "service":
        if not eval_params.service_config_id:
            raise Exception("Service config id is not set. Please set the service config id.")
        config, status_code = await config_service_client.get_config(config_type=ConfigType.SERVICE, config_version=eval_params.service_config_id)

        
    elif requested_config_type == "agent":
        if not eval_params.agent_config_id:
            raise Exception("Agent config id is not set. Please set the agent config id.")
        config, status_code = await config_service_client.get_config(config_type=ConfigType.AGENT, config_version=eval_params.agent_config_id)
    
    if status_code != 200:
        raise Exception(f"Failed to get config: {status_code}")
    
    return config.get("config_body")


def get_preset_config_from_file(requested_config_type: str, eval_params: EvaluationJobConfig):
    """
    Get the preset configuration from a local file.

    Args:
        requested_config_type (str): The type of configuration requested (e.g., "service" or "agent").
        eval_params (EvaluationJobConfig): The parameters provided by the user.

    Returns:
        dict: The preset configuration as a dictionary.
    """
    config = load_file(eval_params.config_file_path, "yaml")

    if requested_config_type == "service":
        return config['service_configs'][0].get("config_body")
    elif requested_config_type == "agent":
        return config['agent_configs'][eval_params.agent_config_id].get("config_body")
    else:
        raise ValueError(f"Unknown config type: {requested_config_type}")