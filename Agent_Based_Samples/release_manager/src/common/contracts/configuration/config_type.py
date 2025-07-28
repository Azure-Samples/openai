# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum


class ConfigType(Enum):
    AGENT = "agent"
    SERVICE = "service"
    SYSTEM = "system"
    EVALUATION = "evaluation"
    # service level configs
    ORCHESTRATOR = "orchestrator"
    SESSION_MANAGER = "session-manager"

    @classmethod
    def get_model(cls, config_type: str):
        # Import here to avoid circular imports
        from common.contracts.configuration.agent_config import AgentConfig
        from common.contracts.configuration.orchestrator_config import (
            OrchestratorServiceConfig,
        )
        from common.contracts.configuration.service_config import ServiceConfig
        from common.contracts.configuration.system_config import SystemConfig
        from common.contracts.configuration.session_manager_config import (
            SessionManagerServiceConfig,
        )
        from common.contracts.configuration.eval_config import EvalConfig

        config_type_to_model = {
            cls.AGENT.value: AgentConfig,
            cls.SERVICE.value: ServiceConfig,
            cls.SYSTEM.value: SystemConfig,
            cls.EVALUATION.value: EvalConfig,
            cls.ORCHESTRATOR.value: OrchestratorServiceConfig,
            cls.SESSION_MANAGER.value: SessionManagerServiceConfig,
        }

        try:
            return config_type_to_model[config_type]
        except KeyError:
            raise ValueError(f"Unknown config type: {config_type}")
