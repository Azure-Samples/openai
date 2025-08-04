# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from requests.models import Response
import logging
import json
import time
from pathlib import Path


class AzureContentUnderstandingClient:
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        subscription_key: str = None,
        token_provider: callable = None,
        x_ms_useragent: str = "azure-ai-content-understanding-python/content_extraction",  # noqa
    ):
        if not subscription_key and not token_provider:
            raise ValueError("Either subscription key or token provider must be provided.")
        if not api_version:
            raise ValueError("API version must be provided.")
        if not endpoint:
            raise ValueError("Endpoint must be provided.")

        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._logger = logging.getLogger(__name__)
        self._headers = self._get_headers(subscription_key, token_provider(), x_ms_useragent)

    def _get_analyzer_url(self, endpoint, api_version, analyzer_id):
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={api_version}"  # noqa

    def _get_analyzer_list_url(self, endpoint, api_version):
        return f"{endpoint}/contentunderstanding/analyzers?api-version={api_version}"

    def _get_analyze_url(self, endpoint, api_version, analyzer_id):
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={api_version}"  # noqa

    def _get_training_data_config(self, storage_container_sas_url, storage_container_path_prefix):
        return {
            "containerUrl": storage_container_sas_url,
            "kind": "blob",
            "prefix": storage_container_path_prefix,
        }

    def _get_headers(self, subscription_key, api_token, x_ms_useragent):
        """Returns the headers for the HTTP requests.
        Args:
            subscription_key (str): The subscription key for the service.
            api_token (str): The API token for the service.
            enable_face_identification (bool): A flag to enable face identification.
        Returns:
            dict: A dictionary containing the headers for the HTTP requests.
        """
        headers = (
            {"Ocp-Apim-Subscription-Key": subscription_key}
            if subscription_key
            else {"Authorization": f"Bearer {api_token}"}
        )
        headers["x-ms-useragent"] = x_ms_useragent
        return headers

    def get_all_analyzers(self):
        """
        Retrieves a list of all available analyzers from the content understanding service.

        This method sends a GET request to the service endpoint to fetch the list of analyzers.
        It raises an HTTPError if the request fails.

        Returns:
            dict: A dictionary containing the JSON response from the service, which includes
                  the list of available analyzers.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = requests.get(
            url=self._get_analyzer_list_url(self._endpoint, self._api_version),
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    def get_analyzer_detail_by_id(self, analyzer_id):
        """
        Retrieves a specific analyzer detail through analyzerid from the content understanding service.
        This method sends a GET request to the service endpoint to get the analyzer detail.

        Args:
            analyzer_id (str): The unique identifier for the analyzer.

        Returns:
            dict: A dictionary containing the JSON response from the service, which includes the target analyzer detail.

        Raises:
            HTTPError: If the request fails.
        """
        response = requests.get(
            url=self._get_analyzer_url(self._endpoint, self._api_version, analyzer_id),
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    def begin_create_analyzer(
        self,
        analyzer_id: str,
        analyzer_template: dict = None,
        analyzer_template_path: str = "",
        training_storage_container_sas_url: str = "",
        training_storage_container_path_prefix: str = "",
    ):
        """
        Initiates the creation of an analyzer with the given ID and schema.

        Args:
            analyzer_id (str): The unique identifier for the analyzer.
            analyzer_template (dict, optional): The schema definition for the analyzer. Defaults to None.
            analyzer_template_path (str, optional): The file path to the analyzer schema JSON file. Defaults to "".
            training_storage_container_sas_url (str, optional): The SAS URL for the training storage container. Defaults to "".
            training_storage_container_path_prefix (str, optional): The path prefix within the training storage container. Defaults to "".

        Raises:
            ValueError: If neither `analyzer_template` nor `analyzer_template_path` is provided.
            requests.exceptions.HTTPError: If the HTTP request to create the analyzer fails.

        Returns:
            requests.Response: The response object from the HTTP request.
        """
        if analyzer_template_path and Path(analyzer_template_path).exists():
            with open(analyzer_template_path, "r") as file:
                analyzer_template = json.load(file)

        if not analyzer_template:
            raise ValueError("Analyzer schema must be provided.")

        if training_storage_container_sas_url and training_storage_container_path_prefix:  # noqa
            analyzer_template["trainingData"] = self._get_training_data_config(
                training_storage_container_sas_url,
                training_storage_container_path_prefix,
            )

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        response = requests.put(
            url=self._get_analyzer_url(self._endpoint, self._api_version, analyzer_id),
            headers=headers,
            json=analyzer_template,
        )
        response.raise_for_status()
        self._logger.info(f"Analyzer {analyzer_id} create request accepted.")
        return response

    def delete_analyzer(self, analyzer_id: str):
        """
        Deletes an analyzer with the specified analyzer ID.

        Args:
            analyzer_id (str): The ID of the analyzer to be deleted.

        Returns:
            response: The response object from the delete request.

        Raises:
            HTTPError: If the delete request fails.
        """
        response = requests.delete(
            url=self._get_analyzer_url(self._endpoint, self._api_version, analyzer_id),
            headers=self._headers,
        )
        response.raise_for_status()
        self._logger.info(f"Analyzer {analyzer_id} deleted.")
        return response

    def begin_analyze(self, analyzer_id: str, file_location: str, file_data):
        """
        Begins the analysis of a file or URL using the specified analyzer.

        Args:
            analyzer_id (str): The ID of the analyzer to use.
            file_location (str): The path to the file or the URL to analyze.

        Returns:
            Response: The response from the analysis request.

        Raises:
            ValueError: If the file location is not a valid path or URL.
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """

        if file_data:
            data = file_data
            headers = {"Content-Type": "application/octet-stream"}
        else:
            data = None
            if Path(file_location).exists():
                with open(file_location, "rb") as file:
                    data = file.read()
                headers = {"Content-Type": "application/octet-stream"}
            elif "https://" in file_location or "http://" in file_location:
                data = {"url": file_location}
                headers = {"Content-Type": "application/json"}
            else:
                raise ValueError("File location must be a valid path or URL.")

        headers.update(self._headers)
        if isinstance(data, dict):
            response = requests.post(
                url=self._get_analyze_url(self._endpoint, self._api_version, analyzer_id),
                headers=headers,
                json=data,
            )
        else:
            response = requests.post(
                url=self._get_analyze_url(self._endpoint, self._api_version, analyzer_id),
                headers=headers,
                data=data,
            )

        response.raise_for_status()
        self._logger.info(f"Analyzing file {file_location} with analyzer: {analyzer_id}")
        return response

    def get_image_from_analyze_operation(self, analyze_response: Response, image_id: str):
        """Retrieves an image from the analyze operation using the image ID.
        Args:
            analyze_response (Response): The response object from the analyze operation.
            image_id (str): The ID of the image to retrieve.
        Returns:
            bytes: The image content as a byte string.
        """
        operation_location = analyze_response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in the analyzer response header.")
        operation_location = operation_location.split("?api-version")[0]
        image_retrieval_url = f"{operation_location}/images/{image_id}?api-version={self._api_version}"
        try:
            response = requests.get(url=image_retrieval_url, headers=self._headers)
            response.raise_for_status()

            assert response.headers.get("Content-Type") == "image/jpeg"

            return response.content
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {e}")
            return None

    def poll_result(
        self,
        response: Response,
        timeout_seconds: int = 120,
        polling_interval_seconds: int = 2,
    ):
        """
        Polls the result of an asynchronous operation until it completes or times out.

        Args:
            response (Response): The initial response object containing the operation location.
            timeout_seconds (int, optional): The maximum number of seconds to wait for the operation to complete. Defaults to 120.
            polling_interval_seconds (int, optional): The number of seconds to wait between polling attempts. Defaults to 2.

        Raises:
            ValueError: If the operation location is not found in the response headers.
            TimeoutError: If the operation does not complete within the specified timeout.
            RuntimeError: If the operation fails.

        Returns:
            dict: The JSON response of the completed operation if it succeeds.
        """
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers.")

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"Operation timed out after {timeout_seconds:.2f} seconds.")

            response = requests.get(operation_location, headers=self._headers)
            response.raise_for_status()
            status = response.json().get("status").lower()
            if status == "succeeded":
                self._logger.info(f"Request result is ready after {elapsed_time:.2f} seconds.")
                return response.json()
            elif status == "failed":
                self._logger.error(f"Request failed. Reason: {response.json()}")
                raise RuntimeError("Request failed.")
            else:
                self._logger.info(f"Request {operation_location.split('/')[-1].split('?')[0]} in progress ...")
            time.sleep(polling_interval_seconds)
