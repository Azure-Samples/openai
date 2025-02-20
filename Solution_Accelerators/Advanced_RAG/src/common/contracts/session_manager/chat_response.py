from typing import List, Optional
from pydantic import BaseModel
from common.contracts.orchestrator.answer import Answer
from common.contracts.common.error import Error

class ChatResponse(BaseModel):
    connection_id: str
    dialog_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    answer: Optional[Answer] = None
    error: Optional[Error] = None