# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from common.contracts.configuration.agent_config import (
    AgentConfig,
    ChatCompletionAgentConfig,
)
from common.contracts.configuration.config_base import ConfigBase
from common.contracts.configuration.create_config import ConfigType
from common.contracts.configuration.service_config import ServiceConfig
from common.contracts.configuration.system_config import SystemConfig


class OrchestratorConfig(BaseModel):
    system_config: Optional[str] = None
    agents_config: Optional[dict[str, str]] = None
    services_config: Optional[List[str]] = None


class OrchestratorServiceConfig(ConfigBase):
    config_type: str = ConfigType.ORCHESTRATOR.value
    config_body: OrchestratorConfig


class ResolvedOrchestratorConfig(BaseModel):
    """
    ResolvedOrchestratorConfig
    This class represents a fully resolved orchestrator configuration, including all referenced configurations.
    Attributes:
        base_config (OrchestratorConfig): The original orchestrator configuration.
        system_config (Optional[SystemConfig]): The resolved system configuration. Defaults to None.
        agent_configs (Dict[str, AgentConfig]): A dictionary of resolved agent configurations, keyed by agent name.
        service_configs (List[ServiceConfig]): A list of resolved service configurations.
    Methods:
        from_base_config(cls, orchestrator_config: OrchestratorConfig) -> "ResolvedOrchestratorConfig":
            Creates a resolved configuration shell from a base orchestrator configuration.
        to_dict(self) -> Dict[str, Any]:
            Converts the resolved configuration into a dictionary representation.
        validate(self):
            Validates the resolved configuration. Ensures that all agent configurations of type
            'ChatCompletionAgentConfig' reference a valid 'service_id' present in the resolved service configurations.
            Raises a ValueError if validation fails.
    """

    """Fully resolved orchestrator configuration with all referenced configs loaded."""

    # Original orchestrator config
    base_config: Optional[OrchestratorConfig] = None

    # Resolved referenced configs
    system_config: Optional[SystemConfig] = None
    agent_configs: Dict[str, AgentConfig] = Field(default_factory=dict)
    service_configs: List[ServiceConfig] = Field(default_factory=list)

    @field_validator("agent_configs", mode="after")
    def validate_agent_configs(cls, agent_configs: Dict[str, AgentConfig]) -> Dict[str, AgentConfig]:
        # Update agent config name to match the agent name in the config body.
        return {config.config_body.agent_name: config for config in agent_configs.values()}

    @classmethod
    def from_base_config(cls, orchestrator_config: OrchestratorConfig) -> "ResolvedOrchestratorConfig":
        """Create a resolved config shell from a base config."""
        return cls(base_config=orchestrator_config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        result = {
            "base_config": self.base_config.model_dump(),
            "agent_configs": {
                config.config_body.agent_name: config.model_dump() for _, config in self.agent_configs.items()
            },
            "service_configs": [config.model_dump() for config in self.service_configs],
        }

        if self.system_config:
            result["system_config"] = self.system_config.model_dump()

        return result

    def validate(self):
        # If agents_config is not None, ensure all SK Agent configs are referencing a valid service_id
        if self.agent_configs:
            # Get all valid service_ids from service_configs
            valid_service_ids = {service.config_body.service_id for service in self.service_configs}

            for agent_name, agent_config in self.agent_configs.items():
                if isinstance(agent_config.config_body, ChatCompletionAgentConfig):
                    sk_settings = agent_config.config_body.sk_prompt_execution_settings
                    if not sk_settings or not sk_settings.service_id:
                        raise ValueError(
                            f"Agent '{agent_name}' of type 'ChatCompletionAgentConfig' must have a valid 'service_id' "
                            f"in 'sk_prompt_execution_settings'."
                        )

                    # Check if the service_id exists in the resolved service configs
                    if sk_settings.service_id not in valid_service_ids:
                        raise ValueError(
                            f"Agent '{agent_name}' references a 'service_id' ({sk_settings.service_id}) that does not "
                            f"exist in the resolved service configurations."
                        )
        return True

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """
        Get the agent configuration for a given agent name.
        Args:
            agent_name (str): The name of the agent.
        Returns:
            Optional[AgentConfig]: The agent configuration if found, otherwise None.
        """
        agent_config = self.agent_configs.get(agent_name)
        if agent_config:
            return agent_config.config_body
        return None
