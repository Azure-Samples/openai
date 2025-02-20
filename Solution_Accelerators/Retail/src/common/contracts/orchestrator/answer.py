from typing import List, Optional

from pydantic import BaseModel


class Answer(BaseModel):
    answer_string: Optional[str] = ""
    data_points: Optional[List[str]] = []
    steps_execution: Optional[dict] = None
    speak_answer: Optional[str] = ""
    speaker_locale: Optional[str] = None
