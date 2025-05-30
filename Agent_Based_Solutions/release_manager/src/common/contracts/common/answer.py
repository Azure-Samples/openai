# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Answer(BaseModel):
    """
    Represents the answer to a user query, including answer as text, data points, and execution steps.

    Attributes:
        answer_string (Optional[str]): The main answer text to the user query.
        is_final (Optional[bool]): Indicates if this is the final answer to the query.
        data_points (Optional[List[str]]): A list of relevant data points or references used to generate the answer.
        steps_execution (Optional[dict]): A dictionary containing execution steps or logs related to the answer generation.
        speak_answer (Optional[str]): Text to be spoken as the answer, if applicable.
        speaker_locale (Optional[str]): Locale for the speaker, if different from the user's locale.
        additional_metadata (Dict[str, Any]): Additional metadata related to the answer, specific to the use-case.
    """

    answer_string: Optional[str] = ""
    is_final: Optional[bool] = False
    data_points: Optional[List[str]] = []
    steps_execution: Optional[dict] = None
    speak_answer: Optional[str] = ""
    speaker_locale: Optional[str] = None
    # This can be used to store any additional information or metadata related to the answer, specific to the use-case.
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)
