# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas


class BlobStoreHelper:
    """
    A utility class for interacting with Azure Blob Storage, including file uploads and SAS URL generation.
    """

    def __init__(self, storage_account_name: str):
        """
        Initialize the BlobStoreHelper with a storage account name and a credential for Microsoft Entra ID authentication.

        :param storage_account_name: Name of the Azure Storage account.
        """
        if not storage_account_name:
            raise ValueError("Storage account name cannot be empty.")

        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=DefaultAzureCredential()
        )

    async def upload_file_and_get_sas_url(self, container_name: str, local_file_path: str, blob_name: str, expiry: Optional[datetime] = None) -> str:
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
            container_client = self.blob_service_client.get_container_client(container_name)

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
            user_delegation_key = self.blob_service_client.get_user_delegation_key(
                key_start_time=start_time,
                key_expiry_time=expiry_time
            )

            # Generate SAS URL
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=container_name,
                blob_name=blob_name,
                user_delegation_key=user_delegation_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time
            )

            return f"{blob_client.url}?{sas_token}"

        except Exception as e:
            raise RuntimeError(f"An error occurred while uploading the file: {str(e)}")