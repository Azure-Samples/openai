# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import base64
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobClient, BlobServiceClient
from pydantic import HttpUrl

from common.telemetry.app_logger import AppLogger


class BlobStoreHelperNotInitializedError(Exception):
    pass


class BlobStoreHelper:
    def __init__(
        self, logger: AppLogger, storage_account_name: str, container_name=None
    ):

        self.logger = logger
        self.storage_account_name = storage_account_name

        if storage_account_name:
            self.blob_client = BlobServiceClient(
                account_url=f"https://{storage_account_name}.blob.core.windows.net",
                credential=DefaultAzureCredential(),
            )
        if container_name:
            self.container_name = container_name
            if self.blob_client:
                self.container_client = self.blob_client.get_container_client(
                    container_name
                )
            else:
                raise BlobStoreHelperNotInitializedError(
                    "Class BlobStoreHelper not initialized with connection string"
                )

    async def upload_image_async(self, image_as_bytes: bytes) -> HttpUrl:
        if not self.container_client:
            raise Exception("Class BlobStoreHelper not initialized with container name")

        file_extension = "jpg"
        start = time.monotonic()
        image_name = "image_" + str(uuid.uuid4()) + "." + file_extension

        blob_client = self.container_client.get_blob_client(image_name)
        image_data = base64.b64decode(image_as_bytes)
        await blob_client.upload_blob(image_data, overwrite=True)

        sas_url = await self.generate_blob_sas_url(blob_name=image_name)

        duration = (time.monotonic() - start) * 1000
        additional_properties = {
            "blob_upload_duration_ms": duration,
            "blob_name": blob_client.blob_name,
        }

        self.logger.info(
            f"Uploaded image to blob store and generated sas url",
            properties=additional_properties,
        )
        return HttpUrl(sas_url)

    async def generate_blob_sas_url(
        self, blob_name: str, expiry: Optional[datetime] = None
    ) -> str:
        blob_client = self.container_client.get_blob_client(blob_name)

        start_time = datetime.now(timezone.utc)
        expiry_time = start_time + timedelta(hours=24) if not expiry else expiry
        user_delegation_key = await self.blob_client.get_user_delegation_key(
            key_start_time=start_time, key_expiry_time=expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=self.storage_account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            user_delegation_key=user_delegation_key,
            expiry=expiry_time,
            start=start_time,
        )

        sas_url = blob_client.url + "?" + sas_token

        self.logger.info(f"Successfully generated sas url for blob {blob_name}.")
        return sas_url

    async def download_image_data(self, sasUrl: str) -> tuple:
        self.logger.info("Starting image download from URL: " + sasUrl)
        try:
            start = time.monotonic()

            blob_client = BlobClient.from_blob_url(sasUrl)

            stream = await blob_client.download_blob(max_concurrency=5)
            data = await stream.readall()

            duration = (time.monotonic() - start) * 1000
            additional_properties = {
                "blob_download_duration_ms": duration,
                "blob_name": blob_client.blob_name,
                "size": len(data),
            }

            self.logger.info(
                f"Downloaded image from blob store", properties=additional_properties
            )

            return blob_client.blob_name, data

        except ClientAuthenticationError as auth_err:
            self.logger.error(
                f"Authentication failed. Could not download blob.\n"
                f"Error details: {auth_err.message}"
            )

        return None, None

    async def upload_file_from_path_and_get_sas_url(
        self,
        container_name: str,
        local_file_path: str,
        blob_name: str,
        expiry: Optional[datetime] = None,
    ) -> str:
        """
        Uploads a file to the specified Azure Blob container and returns a SAS URL for the uploaded blob.
        """
        try:
            # Validate inputs
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"The file '{local_file_path}' does not exist.")
            if not container_name or not blob_name:
                raise ValueError("Container name and blob name cannot be empty.")

            # Get the container client
            container_client = self.blob_client.get_container_client(container_name)

            # Create the container if it does not exist
            if not container_client.exists():
                container_client.create_container()

            # Upload the file
            blob_client = container_client.get_blob_client(blob_name)
            with open(local_file_path, "rb") as file_data:
                blob_client.upload_blob(file_data, overwrite=True)

            # Set start time and end time for SAS URLs, and create a key
            start_time = datetime.now(timezone.utc)
            expiry_time = start_time + timedelta(hours=24) if not expiry else expiry

            return await self.generate_blob_sas_url(blob_name=blob_name, expiry=expiry_time)
        except Exception as e:
            raise RuntimeError(f"An error occurred while uploading the file: {str(e)}")
