# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from pydantic import BaseModel


class ConfigBase(BaseModel):
    config_type: str
    config_version: Optional[str] = None
