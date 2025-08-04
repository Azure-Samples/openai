# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
import json

import redis

from common.clients.caching.caching_client_abstract import CachingClient
from common.clients.services.config_service_client import ConfigServiceClient
from common.contracts.configuration.config_type import ConfigType
from common.exceptions import CacheKeyExistsError, CacheKeyNotFoundError


class RedisCachingClient(CachingClient):
    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        ssl: bool = True,
        decode_responses: bool = True,
        config_service_client: ConfigServiceClient = None,
    ):
        self.redis_client = redis.StrictRedis(
            host=host, port=port, password=password, ssl=ssl, decode_responses=decode_responses
        )
        self.config_service_client = config_service_client
        self.lock = asyncio.Lock()

    async def get(self, config_type: ConfigType, config_version: str) -> str:
        """
        Get the configuration from cache if it exists, otherwise fetch it from the config service and set it in cache.

        Args:
            config_type (ConfigType): The configuration type.
            config_version (str): The configuration version.

        Returns:
            str: The configuration as a JSON string if found, otherwise None.
        """
        key = f"{config_type.value}/{config_version}"
        async with self.lock:
            if self.exists(key):
                return self.redis_client.get(key)

        # Try to get from config service and set in cache
        if config_type == ConfigType.ORCHESTRATOR:
            config_json, status = await self.config_service_client.get_resolved_orchestrator_config(
                config_version=config_version
            )
        else:
            config_json, status = await self.config_service_client.get_config(
                config_type=config_type, config_version=config_version
            )
        if status == 200:
            config_body = json.dumps(config_json.get("config_body"))
            self.set(key, config_body)
            return config_body

        return None

    async def set(self, key: str, value: str) -> None:
        """
        Set the configuration in cache.

        Args:
            key (str): The key for the cache entry.
            value (str): The value to be cached.

        Raises:
            CacheKeyExistsError: If the key already exists in the cache.
        """
        async with self.lock:
            try:
                if not self.exists(key):
                    self.redis_client.set(key, value)
                else:
                    raise CacheKeyExistsError(f"Configuration with key '{key}' already exists in cache")
            except redis.RedisError as e:
                # Log the error or handle it as needed
                print(f"Redis error occurred: {e}")

    def exists(self, key: str) -> bool:
        """
        Check if the configuration exists in cache.

        Args:
            key (str): The key for the cache entry.

        Returns:
            bool: True if the key exists in the cache, False otherwise.
        """
        return self.redis_client.exists(key)

    def delete(self, key: str) -> bool:
        """
        Delete the configuration from cache.

        Args:
            key (str): The key for the cache entry.

        Returns:
            bool: True if the key was successfully deleted, False if the key was not found.

        Raises:
            CacheKeyNotFoundError: If the key does not exist in the cache.
        """
        with self.lock:
            if self.exists(key):
                self.redis_client.delete(key)
                return True
            raise CacheKeyNotFoundError(f"Configuration with key '{key}' not found in cache")
