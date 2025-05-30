# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import BaseModel
from typing import Optional


class OrchestratorServiceOverrides(BaseModel):
    config_version: Optional[str] = None


class SessionManagerServiceOverrides(BaseModel):
    check_safe_image_content: Optional[bool] = True
    config_version: Optional[str] = None


class Overrides(BaseModel):
    orchestrator_runtime: Optional[OrchestratorServiceOverrides] = None
    session_manager_runtime: Optional[SessionManagerServiceOverrides] = None
