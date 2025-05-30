# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from typing import Optional
from pydantic import BaseModel

from common.contracts.configuration.config_base import ConfigBase
from common.contracts.configuration.create_config import ConfigType


class SystemSettings(BaseModel):
    # Placeholder for system settings that are not agent or service specific
    app_name: str


class SystemConfig(ConfigBase):
    config_type: str = ConfigType.SYSTEM.value
    config_body: SystemSettings
