# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import BaseModel
from typing import Optional

from common.contracts.configuration.config_base import ConfigBase
from common.contracts.configuration.create_config import ConfigType


class SessionManagerConfig(BaseModel):
    orchestrator_service_uri: Optional[str] = None


class SessionManagerServiceConfig(ConfigBase):
    config_type: ConfigType = ConfigType.SESSION_MANAGER
    config_body: SessionManagerConfig
