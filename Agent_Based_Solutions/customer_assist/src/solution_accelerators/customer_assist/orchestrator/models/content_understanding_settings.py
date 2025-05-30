# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from dataclasses import dataclass


@dataclass
class ContentUnderstandingSettings:
    """
    Configuration settings for connecting to a Content Understanding Service.

    This class holds the necessary credentials and connection information
    needed to connect to Azure Content Understanding Service.
    """

    endpoint: str
    api_version: str = "2024-12-01-preview"
    subscription_key: str = None

    # Optional attributes for analyzer IDs
    utility_bill_analyzer_id: str = "utility-bill-analyzer"
    drivers_license_analyzer_id: str = "drivers-license-analyzer"
    income_statement_analyzer_id: str = "income-statement-analyzer"
