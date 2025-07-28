# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from typing import Dict, Generic, Optional, TypeVar

from common.telemetry.app_logger import AppLogger

T = TypeVar("T")


class ThreadSafeCache(Generic[T]):
    """
    Handles items in a thread-safe cache.
    """

    def __init__(self, logger: AppLogger):
        """
        Initialize the ThreadSafeCache with an asyncio lock and an empty cache.
        """
        self.logger = logger

        # Initialize thread-safe cache for handling items.
        # TODO: Add support for maximum limit on items.
        self._lock = asyncio.Lock()
        self._cache: Dict[str, T] = {}

    async def add_async(self, key: str, value: T) -> T:
        """
        Add a new item to the cache.

        Raises:
            KeyError: If the key already exists in the cache.
        """
        async with self._lock:
            if key in self._cache:
                self.logger.error(f"Key '{key}' already exists.")
                raise KeyError(f"Key '{key}' already exists.")

            self._cache[key] = value
            self.logger.info(f"Added key '{key}' to the cache.")
            return T

    async def update_async(self, key: str, value: T) -> T:
        """
        Updates an existing item in the cache.

        Raises:
            KeyError: If the key does not exist in the cache.
        """
        async with self._lock:
            if key not in self._cache:
                self.logger.error(f"Key '{key}' does not exist.")
                raise KeyError(f"Key '{key}' does not exists.")

            self._cache[key] = value
            self.logger.info(f"Updated key '{key}' in the cache.")
            return T

    async def get_async(self, key: str) -> Optional[T]:
        """
        Retrieves an entity from the cache.

        Returns:
            The value associated with the key, or None if the key does not exist.
        """
        async with self._lock:
            return self._cache.get(key)

    async def remove_async(self, key: str) -> None:
        """
        Remove a key value pair from the cache.

        Raises:
            KeyError: If the key does not exist in the cache.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.logger.info(f"Removed key '{key}' from the cache.")
            else:
                self.logger.error(f"Key '{key}' not found.")

    async def exists(self, key: str) -> bool:
        """
        Checks if the given key exists in the cache.
        """
        async with self._lock:
            return key in self._cache

    async def get_all_items_async(self) -> Dict[str, T]:
        """
        List all items in the cache.
        """
        async with self._lock:
            # Return a copy in the current state of cache
            items_copy = dict(self._cache)
            self.logger.info(f"Listing all items. Total count: {len(items_copy)}.")
            return items_copy
