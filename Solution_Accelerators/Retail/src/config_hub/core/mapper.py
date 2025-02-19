from enum import Enum
from common.contracts.orchestrator.configuration import OrchestratorServiceConfig
from common.contracts.session_manager.service_configuration import SessionManagerServiceConfig
from common.contracts.skills.azure_ai_search.configuration import AzureAISearchServiceConfig

class ConfigType(Enum):
    ORCHESTRATOR_RUNTIME = OrchestratorServiceConfig
    SEARCH_RUNTIME = AzureAISearchServiceConfig
    SESSION_MANAGER_RUNTIME = SessionManagerServiceConfig
    
    @staticmethod
    def get_model(config_id):
        for config in ConfigType:
            if config.name.lower() == config_id.lower():
                return config.value
        raise ValueError(f"Config type {config_id} not found")
