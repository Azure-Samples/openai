# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from azure.cosmos.aio import CosmosClient

from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError

from typing import Any, Dict, List, Optional, Union


class CosmosConflictError(BaseException):
    pass


class CosmosDBContainer:
    def __init__(
        self,
        database_name: str,
        container_name: str,
        partition_key_name: str,
        client: CosmosClient,
        unique_keys: Optional[List[Dict[str, Any]]] = None,
    ):
        self.database_name = database_name
        self.container_name = container_name
        self.client = client
        self.partition_key_name = partition_key_name
        self.unique_keys = unique_keys
        self.container = None

    @classmethod
    async def create(
        cls,
        database_name: str,
        container_name: str,
        partition_key_name: str,
        client: CosmosClient,
        unique_keys: Optional[List[Dict[str, Any]]] = None,
    ):
        self = cls(
            database_name, container_name, partition_key_name, client, unique_keys
        )
        await self._initialize()
        return self

    async def _initialize(self):
        database = await self.client.create_database_if_not_exists(
            id=self.database_name
        )
        partition_key = PartitionKey(path="/" + self.partition_key_name)
        unique_key_policy = (
            {"uniqueKeys": self.unique_keys} if self.unique_keys is not None else None
        )
        self.container = await database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=partition_key,
            unique_key_policy=unique_key_policy,
        )

    async def create_item(
        self, id: str, partition_key: str, item: Dict[str, Any]
    ) -> Union[Dict[str, Any], Exception]:
        try:
            item["id"] = id
            item[self.partition_key_name] = partition_key

            return await self.container.create_item(item)
        except CosmosHttpResponseError as e:
            if e.status_code == 409:
                raise CosmosConflictError(
                    f"Item with id {id} already exists in container {self.container_name}."
                )
            raise Exception(f"Error creating item in Cosmos DB container: {e.message}.")

    async def get_item(self, id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT * FROM c WHERE c.id = @item_id"
            params: List[Dict[str, object]] = [dict(name="@item_id", value=id)]

            results = self.container.query_items(
                query=query, parameters=params, partition_key=partition_key
            )
            items = [item async for item in results]

            if len(items) == 0:
                return None
            elif len(items) > 1:
                raise Exception(
                    f"Multiple items found with the same id {id} in container {self.container_name}."
                )
            return items[0]
        except CosmosHttpResponseError as e:
            raise Exception(
                f"Error getting item from Cosmos DB container: {e.message}."
            )

    async def get_all_items(self, partition_key: str) -> List[Dict[str, Any]]:
        try:
            query = "SELECT * FROM c"

            results = self.container.query_items(
                query=query, partition_key=partition_key
            )
            items = [item async for item in results]

            return items
        except CosmosHttpResponseError as e:
            raise Exception(
                f"Error getting all items from Cosmos DB container: {e.message}."
            )

    async def upsert_item(
        self, id: str, partition_key: str, item: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            item["id"] = id
            item[self.partition_key_name] = partition_key
            return await self.container.upsert_item(item)
        except CosmosHttpResponseError as e:
            raise Exception(f"Error updating item in Cosmos DB container: {e.message}.")

    async def delete_item(self, id: str, partition_key):
        try:
            item = await self.get_item(id, partition_key)
            if item is not None:
                await self.container.delete_item(item, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            raise Exception(
                f"Error deleting item from Cosmos DB container: {e.message}."
            )

    async def query_items(
        self, query: str, params: List[Dict[str, object]], partition_key: str
    ) -> List[Dict[str, Any]]:
        try:
            results = self.container.query_items(
                query=query, parameters=params, partition_key=partition_key
            )
            return [item async for item in results]
        except CosmosHttpResponseError as e:
            raise Exception(
                f"Error executing query on Cosmos DB container: {e.message}."
            )
