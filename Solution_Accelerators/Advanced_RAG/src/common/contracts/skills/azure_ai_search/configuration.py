
from common.contracts.config_hub.config_base import ConfigBase
from common.contracts.skills.azure_ai_search.config_models import CognitiveSearchSkillConfig

class AzureAISearchServiceConfig(ConfigBase):
    config_body: CognitiveSearchSkillConfig
    config_id: str = "search_runtime"