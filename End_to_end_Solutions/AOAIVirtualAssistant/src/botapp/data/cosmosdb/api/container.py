import os
from typing import Any, Dict, List, Optional
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError
from config import DefaultConfig

class CosmosDBContainer:
    def __init__(self, database_name: str, container_name: str, partition_key: str, unique_keys: Optional[List[Dict[str, Any]]] = None):
        database_name = database_name
        self.container_name = container_name
        client = CosmosClient(url=DefaultConfig.COSMOS_DB_ENDPOINT, credential=DefaultConfig.COSMOS_DB_KEY)
        database = client.create_database_if_not_exists(id=database_name)
        self.partition_key = PartitionKey(path="/" + partition_key)
        unique_key_policy = { 'uniqueKeys': unique_keys } if unique_keys is not None else None
        self.container = database.create_container_if_not_exists(id=container_name, partition_key=self.partition_key, unique_key_policy=unique_key_policy)

    def create_item(self, id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item["id"] = id
            return self.container.create_item(item)
        except CosmosHttpResponseError as e:
            raise Exception("Error creating item in Cosmos DB container.")
        
    def get_item(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT * FROM c WHERE c.id = @item_id"
            params: List[Dict[str, object]] = [
                dict(name="@item_id", value=id)
            ]

            results = self.container.query_items(
                query=query, parameters=params, partition_key=id
            )
            items = [item for item in results]

            if len(items) == 0:
                return None
            elif len(items) > 1:
                raise Exception("Multiple items found with the same id " + id + " in container " + self.container_name + ".")
            return items[0]
        except CosmosHttpResponseError as e:
            raise Exception("Error getting item from Cosmos DB container.")
        
    def update_item(self, id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item["id"] = id
            return self.container.replace_item(id, item)
        except CosmosHttpResponseError as e:
            raise Exception("Error updating item in Cosmos DB container.")
        
    def delete_item(self, id: str):
        try:
            item = self.get_item(id)
            if item is not None:
                self.container.delete_item(item, partition_key=id)
        except CosmosHttpResponseError as e:
            raise Exception("Error deleting item from Cosmos DB container.")        