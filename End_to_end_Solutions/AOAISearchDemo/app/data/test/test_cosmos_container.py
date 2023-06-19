import copy
import unittest

from cosmosdb.container import CosmosDBContainer
from typing import List, Dict, Any, Optional, Iterable
from unittest.mock import Mock

def create_item(item: dict) -> Dict[str, Any]:
    return copy.deepcopy(item)

def create_item_raise_exception(item: dict):
    raise Exception("Test exception.")

def query_items(query: str, parameters: Optional[List[Dict[str, Any]]], partition_key: Optional[Any]) -> Iterable[Dict[str, Any]]:
    return [{"property1": "value1", "property2": "value2"}]

def query_items_no_item(query: str, parameters: Optional[List[Dict[str, Any]]], partition_key: Optional[Any]) -> Iterable[Dict[str, Any]]:
    return []

def query_items_multiple_items(query: str, parameters: Optional[List[Dict[str, Any]]], partition_key: Optional[Any]) -> Iterable[Dict[str, Any]]:
    return [{"property1": "value1", "property2": "value2"}, {"property3": "value3"}]

def query_items_raise_exception(query: str, parameters: Optional[List[Dict[str, Any]]], partition_key: Optional[Any]) -> Iterable[Dict[str, Any]]:
    raise Exception("Test exception.")

def replace_item(item: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(body)

def replace_item_raise_exception(item: str, body: Dict[str, Any]) -> Dict[str, Any]:
    raise Exception("Test exception.")

def delete_item(item: Dict[str, Any], partition_key: str):
    pass

def delete_item_raise_exception(item: Dict[str, Any], partition_key: str):
    raise Exception("Test exception.")

class CosmosDBContainerTests(unittest.TestCase):
    def test_create_item(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.create_item.side_effect = create_item
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test
        item = {"property1": "value1", "property2": "value2"}
        created_item = container.create_item("id", "partition_key", item)

        # assert container proxy was called as expected and returned item is as expected 
        expected_item = {"property1": "value1", "property2": "value2", "id": "id", "partition_key_name": "partition_key"}
        cosmos_container_proxy.create_item.assert_called_once_with(expected_item)
        self.assertDictEqual(created_item, expected_item)

    def test_create_item_raises_exception(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.create_item.side_effect = create_item_raise_exception
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test and assert container client caught and reraised exception 
        with self.assertRaises(Exception):
            item = {"property1": "value1", "property2": "value2"}
            container.create_item("id", "partition_key", item)

    def test_get_item(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.query_items.side_effect = query_items
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test
        id = "id"
        partition_key = "partition_key"
        retrieved_item = container.get_item(id, partition_key)

        # assert container proxy was called as expected and returned item is as expected 
        expected_item = {"property1": "value1", "property2": "value2"}
        cosmos_container_proxy.query_items.assert_called_once_with(query='SELECT * FROM c WHERE c.id = @item_id', parameters=[{'name': '@item_id', 'value': id}], partition_key=partition_key)
        self.assertIsNotNone(retrieved_item)
        if retrieved_item is not None:
            self.assertDictEqual(expected_item, retrieved_item)

    def test_get_item_returns_none(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.query_items.side_effect = query_items_no_item
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test
        id = "id"
        partition_key = "partition_key"
        retrieved_item = container.get_item(id, partition_key)

        # assert container proxy was called as expected and returned item is None as expected 
        cosmos_container_proxy.query_items.assert_called_once_with(query='SELECT * FROM c WHERE c.id = @item_id', parameters=[{'name': '@item_id', 'value': id}], partition_key=partition_key)
        self.assertIsNone(retrieved_item)

    def test_get_item_returns_multiple(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.query_items.side_effect = query_items_multiple_items
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test and assert container proxy was called as expected and container client caught and reraised exception
        id = "id"
        partition_key = "partition_key"
        with self.assertRaises(Exception):
            container.get_item(id, partition_key)
            cosmos_container_proxy.query_items.assert_called_once_with(query='SELECT * FROM c WHERE c.id = @item_id', parameters=[{'name': '@item_id', 'value': id}], partition_key=partition_key)

    def test_get_item_raises_exception(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.query_items.side_effect = query_items_raise_exception
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test and assert container client caught and reraised exception 
        with self.assertRaises(Exception):
            container.get_item("id", "partition_key")

    def test_update_item(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.replace_item.side_effect = replace_item
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test
        item = {"property1": "value1", "property2": "value2"}
        replacement_item = container.update_item("id", "partition_key", item)

        # assert container proxy was called as expected and returned replacement item as expected 
        cosmos_container_proxy.replace_item.assert_called_once_with("id", item)
        self.assertDictEqual(item, replacement_item)

    def test_update_item_raises_exception(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.replace_item.side_effect = replace_item_raise_exception
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test and assert container client caught and reraised exception 
        with self.assertRaises(Exception):
            item = {"property1": "value1", "property2": "value2"}
            container.update_item("id", "partition_key", item)

    def test_delete_item(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.delete_item.side_effect = delete_item
        cosmos_container_proxy.query_items.side_effect = query_items
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test
        id = "id"
        partition_key = "partition_key"
        container.delete_item(id, partition_key)

        # assert container proxy was called as expected
        item = {"property1": "value1", "property2": "value2"}
        cosmos_container_proxy.query_items.assert_called_once_with(query='SELECT * FROM c WHERE c.id = @item_id', parameters=[{'name': '@item_id', 'value': id}], partition_key=partition_key)
        cosmos_container_proxy.delete_item.assert_called_once_with(item, partition_key=partition_key)        

    def test_delete_item_raises_exception(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.delete_item.side_effect = delete_item_raise_exception
        cosmos_container_proxy.query_items.side_effect = query_items
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test and assert container proxy was called as expected and container client caught and reraised exception 
        with self.assertRaises(Exception):
            id = "id"
            partition_key = "partition_key"
            container.delete_item(id, partition_key)
            item = {"property1": "value1", "property2": "value2"}
            cosmos_container_proxy.query_items.assert_called_once_with(query='SELECT * FROM c WHERE c.id = @item_id', parameters=[{'name': '@item_id', 'value': id}], partition_key=id)
            cosmos_container_proxy.delete_item.assert_called_once_with(item, partition_key=id)

    def test_query_items(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.query_items.side_effect = query_items
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test
        query = "query"
        params: List[Dict[str, object]] = [
            dict(name="@property1", value="value1")
        ]
        partition_key = "partition_key"
        retrieved_items = container.query_items(query, params, partition_key)

        # assert container proxy was called as expected and returned item is as expected 
        expected_item = {"property1": "value1", "property2": "value2"}
        cosmos_container_proxy.query_items.assert_called_once_with(query=query, parameters=params, partition_key=partition_key)
        self.assertTrue(len(retrieved_items) == 1)
        self.assertDictEqual(expected_item, retrieved_items[0])

    def test_query_items_raises_exception(self):
        # set up container with mocked dependencies
        cosmos_container_proxy = Mock()
        cosmos_container_proxy.query_items.side_effect = query_items_raise_exception
        cosmos_database_proxy = Mock()
        cosmos_database_proxy.create_container_if_not_exists.return_value = cosmos_container_proxy
        cosmos_client_mock = Mock()
        cosmos_client_mock.create_database_if_not_exists.return_value = cosmos_database_proxy
        container = CosmosDBContainer("database_name", "container_name", "partition_key_name", cosmos_client_mock)

        # run test and assert container client caught and reraised exception 
        with self.assertRaises(Exception):
            container.query_items("id", "partition_key")

if __name__ == '__main__':
    unittest.main()
