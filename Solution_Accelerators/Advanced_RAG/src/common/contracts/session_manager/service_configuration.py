
from common.contracts.config_hub.config_base import ConfigBase
from common.contracts.configuration_enum import ConfigurationEnum
from common.contracts.session_manager.session_manager_config_model import SessionManagerConfig

class SessionManagerServiceConfig(ConfigBase):
    config_id: str = ConfigurationEnum.SESSION_MANAGER_RUNTIME.value
    config_body: SessionManagerConfig
    