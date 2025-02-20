# from pydantic import BaseModel, Base64Str
# from enum import Enum
# from typing import List, Optional,Literal

# # These are the classes from common.contracts.data.chat_session used here for integration testing as well.

# class UserPromptPayload(BaseModel):
#     type: Literal['text', 'image', 'product']
#     value: str # either user utterance or base64 encoded image data

# class UserGender(str, Enum):
#     Male = "Male",
#     Female = "Female",
#     Other = "Other"

# class UserProfle(BaseModel):
#     id: str;
#     user_name: str;
#     description: Optional[str] = None;
#     gender: Optional[UserGender] = "Other";
#     age: Optional[int] = None;


# class SearchOverrides(BaseModel):
#     semantic_ranker: Optional[bool] = True
#     vector_search: Optional[bool] = True
#     top: Optional[int] = 7

# class Overrides(BaseModel):
#     is_content_safety_enabled: Optional[bool] = True
#     search_overrides: Optional[SearchOverrides] = SearchOverrides()

# # from common.contracts.data.chat_session import UserPrompt, Overrides, UserProfle
# """User prompt contains text and image data in sequence they were added by the user"""
# class UserPrompt(BaseModel, extra="allow"):
#     payload: List[UserPromptPayload] = []

#     def add_text_payload(self, text: str):
#         text_payload = UserPromptPayload(type='text', value=text)
#         self.payload.append(text_payload)

#     def add_image_data_payload(self, image_data: Base64Str):
#         image_data_payload = UserPromptPayload(type='image', value=image_data)
#         self.payload.append(image_data_payload)

#     def add_product_payload(self, product_id: str):
#         product_payload = UserPromptPayload(type='product', value=product_id)
#         self.payload.append(product_payload)


# """Message from UI that can contain text and image data in sequence they were added by the user"""
# class UIMessage(BaseModel, extra="allow"):
#     user_prompt: UserPrompt
#     user_id: str = 'anonymous'
#     conversation_id: str
#     dialog_id: str
#     overrides: Overrides = Overrides()
#     user_profile: Optional[UserProfle] = None

# class SessionManagerRagRequest(BaseModel, extra="allow"):
#     user_id: str
#     conversation_id: str
#     dialog_id: str
#     dialog: str
#     overrides: Overrides = Overrides()
#     scenario: str = "rag"


# class SessionManagerRetailRequest(BaseModel, extra="allow"):
#     user_id: str
#     conversation_id: str
#     dialog_id: str
#     overrides: Overrides = Overrides()
#     scenario: str = "retail"
#     user_prompt: UserPrompt
