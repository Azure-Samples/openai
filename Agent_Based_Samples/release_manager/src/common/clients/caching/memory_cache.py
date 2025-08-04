# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import asyncio
from common.clients.caching.caching_client_abstract import CachingClient
from common.clients.services.config_service_client import ConfigServiceClient
from common.exceptions import CacheKeyExistsError, CacheKeyNotFoundError


class InMemoryCachingClient(CachingClient):
    def __init__(self, config_service_client: ConfigServiceClient):
        self.cache = {}
        self.config_service_client = config_service_client
        self.lock = asyncio.Lock()

    async def get(self, config_type: str, config_version: str) -> str:
        """
        Get the configuration from cache if it exists, otherwise fetch it from the config service and set it in cache

        Args:
            config_type (str): The configuration type.
            config_version (str): The configuration version.

        Returns:
            str: The configuration as a JSON string if found, otherwise None.
        """
        key = f"{config_type}/{config_version}"
        async with self.lock:
            if self.exists(key):
                return self.cache.get(key)

        # Try get from config service and set in cache
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
            CacheKeyExsistsError: If the key already exists in the cache.
        """
        async with self.lock:
            if not self.exists(key):
                self.cache[key] = value
            else:
                raise CacheKeyExistsError(f"Configuration with key {key} already exists in cache")

    def exists(self, key: str) -> bool:
        """
        Check if the configuration exists in cache

        Args:
            key (str): The key for the cache entry.

        Returns:
            bool: True if the key exists in the cache, False otherwise.
        """
        return key in self.cache

    async def delete(self, key: str) -> bool:
        """
        Delete the configuration from cache.

        Args:
            key (str): The key for the cache entry.

        Returns:
            bool: True if the key was successfully deleted, False if the key was not found.
        """
        async with self.lock:
            if self.exists(key):
                del self.cache[key]
                return True

            raise CacheKeyNotFoundError(f"Configuration with key {key} not found in cache")
