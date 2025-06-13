# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


class InvalidConsentError(Exception):
    """Exception raised when consent is invalid or missing."""

    def __init__(self, message="Invalid or missing consent."):
        super().__init__(message)
