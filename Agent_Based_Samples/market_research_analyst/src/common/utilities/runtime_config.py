# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json

from common.clients.caching.azure_redis_cache import RedisCachingClient
from common.contracts.configuration.config_type import ConfigType
from common.contracts.configuration.orchestrator_config import (
    ResolvedOrchestratorConfig,
)
from common.contracts.orchestrator.request import Request
from common.telemetry.app_logger import AppLogger


async def get_orchestrator_runtime_config(
    default_runtime_config, caching_client: RedisCachingClient, request: Request, logger: AppLogger
) -> ResolvedOrchestratorConfig:
    """
    Fetches the orchestrator runtime configuration, applying overrides if available.

    Args:
        default_runtime_config: The default runtime configuration.
        caching_client: The caching client to fetch overrides from.
        request: The request containing potential overrides.
        logger: Logger for logging information and errors.

    Returns:
        ResolvedOrchestratorConfig: The resolved runtime configuration.
    """
    orchestrator_config = default_runtime_config

    try:
        # Check for overrides in the request
        if request.overrides and request.overrides.orchestrator_runtime:
            config_version = request.overrides.orchestrator_runtime.config_version
            orchestrator_overrides_json = await caching_client.get(
                config_type=ConfigType.ORCHESTRATOR,
                config_version=config_version,
            )

            if orchestrator_overrides_json:
                orchestrator_config = json.loads(orchestrator_overrides_json)
                logger.info(f"Orchestrator runtime config overrides found in cache for version {config_version}")
            else:
                logger.info(f"Orchestrator runtime config overrides not found in cache for version {config_version}")

        return ResolvedOrchestratorConfig(**orchestrator_config)

    except Exception as e:
        logger.error(f"Error fetching orchestrator runtime config: {e}")
        raise
