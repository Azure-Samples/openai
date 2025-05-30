# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from dataclasses import dataclass


@dataclass
class VisualizationSettings:
    """
    Configuration settings for data visualization.

    Attributes:
        storage_account_name (str): The name of the Azure storage account.
        visualization_data_blob_container (str): The name of the blob container for visualization data.
    """
    storage_account_name: str
    visualization_data_blob_container: str