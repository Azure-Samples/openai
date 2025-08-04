# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from abc import ABC, abstractmethod


class CachingClient(ABC):
    @abstractmethod
    async def get(self, config_type, config_version) -> str:
        pass

    @abstractmethod
    async def set(self, key: str, value: str):
        pass
