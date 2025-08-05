# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from typing import Optional

from common.contracts.configuration.config_type import ConfigType
from pydantic import (
    BaseModel,
    ValidationInfo,
    field_validator,
    ValidationError,
    validator,
)


class CreateConfigRequest(BaseModel):
    config_type: Optional[ConfigType] = None
    config_version: Optional[str] = None
    config_body: dict = {}


class CreateConfigResponse(BaseModel):
    config_type: str = ""
    config_version: str = ""
    error: str = ""

    def to_dict(self):
        return self.model_dump()
