# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional

from pydantic import BaseModel


class Error(BaseModel):
    """"
    Represents an error that occurred during processing a user query.

    Attributes:
        error_str (Optional[str]): A string describing the error that occurred.
        retry (Optional[bool]): Indicates whether the operation can be retried. Defaults to None.
        status_code (Optional[int]): HTTP status code associated with the error. Defaults to 500.
    """
    error_str: Optional[str] = None
    retry: Optional[bool] = None
    status_code: Optional[int] = 500