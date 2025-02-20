from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from common.contracts.common.overrides import Overrides
from common.contracts.common.user_prompt import UserPrompt
from common.contracts.common.user_profile import UserProfile


class ResultAssertion(BaseModel):
    result_count: Optional[str] = None
    product_description_includes_keywords: Optional[List[str]]


class Assertion(BaseModel):
    response_assertion: Optional[str] = None
    result_assertion: Optional[ResultAssertion] = None
    check_presence_citation: Optional[bool] = False


class TestDialog(BaseModel):
    __test__ = False
    dialog_id: str
    message: UserPrompt
    overrides: Optional[Overrides]
    assertion: Optional[Assertion]


class TestConversation(BaseModel):
    __test__ = False
    conversation_id: str
    user_id: str
    dialogs: List[TestDialog]
    user_profile: Optional[UserProfile] = None


class TestCase(BaseModel):
    __test__ = False
    test_case: str
    conversation: TestConversation
    communication_protocol: Literal["http", "websocket", "all"] = Field(default="http")
    scenario: str = "rag"
