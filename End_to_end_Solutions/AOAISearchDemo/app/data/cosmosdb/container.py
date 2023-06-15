from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError
from typing import Any, Dict, List, Optional

class CosmosConflictError(BaseException):
    pass

class CosmosDBContainer:
    def __init__(self, database_name: str, container_name: str, partition_key_name: str, client: CosmosClient, unique_keys: Optional[List[Dict[str, Any]]] = None):
        database_name = database_name
        self.container_name = container_name
        self.client = client
        database = client.create_database_if_not_exists(id=database_name)
        self.partition_key_name = partition_key_name
        partition_key = PartitionKey(path="/" + partition_key_name)
        unique_key_policy = { 'uniqueKeys': unique_keys } if unique_keys is not None else None
        self.container = database.create_container_if_not_exists(id=container_name, partition_key=partition_key, unique_key_policy=unique_key_policy)

    def create_item(self, id: str, partition_key: str, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item["id"] = id
            item[self.partition_key_name] = partition_key

            return self.container.create_item(item)
        except CosmosHttpResponseError as e:
            if e.status_code == 409:
                raise CosmosConflictError(f"Item with id {id} already exists in container {self.container_name}.")
            raise Exception(f"Error creating item in Cosmos DB container: {e.message}.")
        
    def get_item(self, id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT * FROM c WHERE c.id = @item_id"
            params: List[Dict[str, object]] = [
                dict(name="@item_id", value=id)
            ]

            results = self.container.query_items(
                query=query, parameters=params, partition_key=partition_key
            )
            items = [item for item in results]

            if len(items) == 0:
                return None
            elif len(items) > 1:
                raise Exception(f"Multiple items found with the same id {id} in container {self.container_name}.")
            return items[0]
        except CosmosHttpResponseError as e:
            raise Exception(f"Error getting item from Cosmos DB container: {e.message}.")
        
    def get_all_items(self, partition_key: str) -> List[Dict[str, Any]]:
        try:
            query = "SELECT * FROM c"

            results = self.container.query_items(query=query, partition_key=partition_key)
            items = [item for item in results]

            return items
        except CosmosHttpResponseError as e:
            raise Exception(F"Error getting all items from Cosmos DB container: {e.message}.")
        
    def update_item(self, id: str, partition_key: str, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item["id"] = id
            item[self.partition_key_name] = partition_key
            return self.container.replace_item(id, item)
        except CosmosHttpResponseError as e:
            raise Exception(f"Error updating item in Cosmos DB container: {e.message}.")
        
    def delete_item(self, id: str, partition_key):
        try:
            item = self.get_item(id, partition_key)
            if item is not None:
                self.container.delete_item(item, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            raise Exception(f"Error deleting item from Cosmos DB container: {e.message}.")
        
    def query_items(self, query: str, params: List[Dict[str, object]], partition_key: str) -> List[Dict[str, Any]]:
        try:
            results = self.container.query_items(
                query=query, parameters=params, partition_key=partition_key
            )
            return [item for item in results]
        except CosmosHttpResponseError as e:
            raise Exception(f"Error executing query on Cosmos DB container: {e.message}.")