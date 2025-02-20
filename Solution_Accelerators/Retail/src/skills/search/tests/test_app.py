import os
import json
import unittest

from dotenv import load_dotenv
from fastapi.testclient import TestClient

import os
import re
import sys
# Sys path needs to be modified for app.py imports to work without additional changes``
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src")))

from src.app import app, ImageSearchResponse, ImageCategoriesResponse, ImageCategorySummaryResponse


class CommonTestsSetup(unittest.TestCase):
    def setUp(self):
        # Load env vars
        env_var_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", ".env"))
        if not os.path.exists(env_var_path):
            raise ValueError(".env var file not found")

        load_dotenv(env_var_path)

        # Create client
        self.client = TestClient(app)

    def assert_valid_guid(self, guid: str):
        # Regular expression for matching a GUID pattern
        guid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        if not guid_pattern.match(guid):
            raise AssertionError(f"'{guid}' is not a valid GUID")


class CognitiveSearchAppValidation(CommonTestsSetup):
    def test_empty_route_non_supported_method(self):
        # Arrange & Act
        response = self.client.get("/")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_empty_route_supported_method(self):
        # Arrange & Act
        response = self.client.post("/")

        # Assert
        self.assertEqual(response.status_code, 404)




class CognitiveSearchImageSearchPost(CommonTestsSetup):
    image_route = "/imageSearch"

    def test_image_search_get_non_supported_method(self):
        # Arrange & Act
        response = self.client.get(self.image_route)

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_image_search_post_no_payload(self):
        # Arrange & Act
        response = self.client.post(self.image_route)

        # Assert
        self.assertEqual(response.status_code, 422)

    def test_image_search_post_empty_payload(self):
        # Arrange & Act
        body = {}
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 422)

    def test_image_search_post_payload_empty_list(self):
        # Arrange
        body = {"search_queries": []}

        # Act
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_image_search_post_payload_list_item_incomplete(self):
        # Arrange
        body = {"search_queries": [{}]}

        # Act
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 422)

    def test_image_search_post_payload_list_item_query_empty(self):
        # Arrange
        body = {"search_queries": [{"search_query": ""}]}

        # Act
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_image_search_post_payload_single_item(self):
        # Arrange
        body = {"search_queries": [{"search_query": "blue pants"}]}

        # Act
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 200)
        response_model = ImageSearchResponse.model_validate(response.json())
        self.assertIs(len(response_model.results), 1)

    def test_image_search_post_payload_multiple_items(self):
        # Arrange
        body = {
            "search_queries": [
                {"search_query": "blue pants"},
                {"search_query": "pink dress"},
                {"search_query": "green beanie"},
            ]
        }

        # Act
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 200)
        response_model = ImageSearchResponse.model_validate(response.json())
        self.assertIs(len(response_model.results), 3)

    def test_image_search_post_payload_3_items_1_fixed_search_id(self):
        # Arrange
        fixed_search_id = "some_specific_search_id"
        body = {
            "search_queries": [
                {"search_query": "blue pants"},
                {"search_query": "pink dress"},
                {"search_query": "green beanie", "search_id": fixed_search_id},
            ]
        }

        # Act
        response = self.client.post(self.image_route, data=json.dumps(body))

        # Assert
        self.assertEqual(response.status_code, 200)
        response_model = ImageSearchResponse.model_validate(response.json())
        self.assertIs(len(response_model.results), 3)
        self.assert_valid_guid(response_model.results[0].search_id)
        self.assert_valid_guid(response_model.results[1].search_id)
        self.assertEqual(response_model.results[2].search_id, fixed_search_id)

class CognitiveSearchImageCategoriesGet(CommonTestsSetup):
    image_route = "/imageSearch/categories"

    def test_image_categories_post_non_supported_method(self):
        # Arrange & Act
        response = self.client.post(self.image_route)

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_image_categories_get(self):
        # Arrange & Act
        response = self.client.get(self.image_route)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_model = ImageCategoriesResponse.model_validate(response.json())
        self.assertTrue(len(response_model.results) > 0)

class CognitiveSearchImageCategoriesSummaryGet(CommonTestsSetup):
    image_route = "/imageSearch/categories/summary"

    def test_image_categories_summary_post_non_supported_method(self):
        # Arrange & Act
        response = self.client.post(self.image_route)

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_image_categories_summary_get(self):
        # Arrange & Act
        response = self.client.get(self.image_route)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_model = ImageCategorySummaryResponse.model_validate(response.json())
        self.assertTrue(len(response_model.results) > 0)