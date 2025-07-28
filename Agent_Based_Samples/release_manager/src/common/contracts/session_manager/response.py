# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from pydantic import BaseModel

from common.contracts.common.answer import Answer
from common.contracts.common.error import Error


class Response(BaseModel):
    """
    Represents the response from the session manager after processing a user query.

    Attributes:
        session_id (str): Unique identifier for the session.
        dialog_id (str): Unique identifier for the dialog.
        user_id (Optional[str]): Identifier for the user, defaults to None if not provided.
        answer (Optional[Answer]): The answer object containing response data, if successful.
        error (Optional[Error]): The error object containing error details, if any occurred.
    """

    session_id: str
    dialog_id: str
    user_id: Optional[str] = None
    answer: Optional[Answer] = None
    error: Optional[Error] = None
