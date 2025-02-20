
from common.contracts.config_hub.config_base import ConfigBase
from common.contracts.configuration_enum import ConfigurationEnum
from common.contracts.orchestrator.bot_config_model import RAGOrchestratorBotConfig

class OrchestratorServiceConfig(ConfigBase):
    config_id: str = ConfigurationEnum.ORCHESTRATOR_RUNTIME.value
    config_body: RAGOrchestratorBotConfig
    