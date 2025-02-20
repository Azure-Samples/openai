from azure.cosmos.aio import CosmosClient
from common.clients.cosmosdb.container import CosmosDBContainer, CosmosConflictError
from common.contracts.config_hub.create_config import CreateConfigRequest
from core.mapper import ConfigType
from typing import Any, List, AnyStr, Optional
from common.telemetry.app_logger import AppLogger
from pydantic import ValidationError

class ConfigurationManager:
    PARTITION_KEY_NAME = "config_id"
    UNIQUE_KEYS = [
        {"paths": [f"/config_version"]}]

    def __init__(self, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_entities_container_name: str, logger: AppLogger) -> None:
        self.cosmos_db_endpoint = cosmos_db_endpoint
        self.cosmos_db_credential = cosmos_db_credential
        self.cosmos_db_name = cosmos_db_name
        self.cosmos_db_entities_container_name = cosmos_db_entities_container_name
        self.logger = logger
        
        self.cosmos_client = CosmosClient(url=cosmos_db_endpoint, credential=cosmos_db_credential, consistency_level="Session")
        self.container = None
    
    @classmethod
    async def create(cls, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_entities_container_name: str, logger: AppLogger):
        self =cls(cosmos_db_endpoint, cosmos_db_credential, cosmos_db_name, cosmos_db_entities_container_name, logger)
        await self._initialize_container()
        return self

    async def _initialize_container(self):
        cosmos_client = CosmosClient(url=self.cosmos_db_endpoint, credential=self.cosmos_db_credential, consistency_level="Session")
        self.container = await CosmosDBContainer.create(
            self.cosmos_db_name, 
            self.cosmos_db_entities_container_name, 
            self.PARTITION_KEY_NAME, 
            cosmos_client, 
            self.UNIQUE_KEYS
        )
        
    async def create_config(self, configuration_data: CreateConfigRequest,) -> Any:
        try:
            created_item = await self.container.create_item(id=configuration_data.config_version,
                                                      partition_key=configuration_data.config_id, 
                                                      item=configuration_data.model_dump())
            
            # Filter out private attributes created by cosmos db
            created_item_filtered = {k: v for k, v in created_item.items() if not k.startswith("_")}
            return created_item_filtered
        except CosmosConflictError:
            raise CosmosConflictError(f"Configuration version already exists in {configuration_data.config_id}.")
    
    async def get_config_version(self, config_version: str, config_id: str) -> Any:
        item = await self.container.get_item(config_version, config_id)
        
        if item is None:
            return None
        
        config_type = ConfigType.get_model(config_id)
        return config_type(**item)

    async def list_configs_by_id(self, config_id: str) -> Any:
        items = await self.container.get_all_items(partition_key=config_id)
        config_type = ConfigType.get_model(config_id)
        configuration_versions: List[AnyStr] = []

        for item in items:
            try:
                configuration_versions.append(config_type(**item).config_version)
            except ValidationError as e:
                self.logger.error(f"Error parsing configuration version: {e}")

        return configuration_versions