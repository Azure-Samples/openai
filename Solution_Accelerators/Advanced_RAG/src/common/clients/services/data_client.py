import json
from common.clients.services.client import make_request, HttpMethod
from common.contracts.common.conversation import Conversation, Dialog
from common.contracts.common.user_profile import UserProfile
from common.telemetry.app_logger import AppLogger
from typing import List

class DataClient():
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger
        
    def check_chat_session(self, user_id: str, conversation_id: str) -> bool:
        path = f"/check-chat-session/{user_id}/{conversation_id}"
        path = f"/check-chat-session/{user_id}/{conversation_id}"
        json_chat_session, _ = make_request(self.base_uri, path, HttpMethod.GET, self.logger)

        if json_chat_session == 'true':
            return True
        else:
            return False

    def create_chat_session(self, user_id: str, conversation_id: str, initial_conversation: Conversation) -> Conversation:
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        payload = initial_conversation.model_dump()
        json_chat_session, _ = make_request(self.base_uri, path, HttpMethod.POST, self.logger, payload)
        data = json.loads(json_chat_session)
        return Conversation(**data)

    def get_chat_session(self, user_id: str, conversation_id: str) -> Conversation:
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        json_chat_session, _ = make_request(self.base_uri, path, HttpMethod.GET, self.logger)
        data = json.loads(json_chat_session)
        return Conversation(**data)
    
    def add_dialog_to_chat_session(self, user_id: str, conversation_id: str, dialog: Dialog) -> Conversation:
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        payload = dialog.model_dump()
        json_chat_session, _ = make_request(self.base_uri, path, HttpMethod.PUT, self.logger, payload)
        data = json.loads(json_chat_session)
        return Conversation(**data)
    
    def clear_chat_session(self, user_id: str, conversation_id: str):
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        make_request(self.base_uri, path, HttpMethod.DELETE, self.logger)

    def create_user_profile(self, user_id: str, user_name: str, description: str) -> UserProfile:
        path = f"/user-profiles/{user_id}"
        payload = {
            "user_name": user_name,
            "description": description
        }
        json_user_profile, _ = make_request(self.base_uri, path, HttpMethod.POST, self.logger, payload)
        return UserProfile(**json.loads(json_user_profile))
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        path = f"/user-profiles/{user_id}"
        json_user_profile, _ = make_request(self.base_uri, path, HttpMethod.GET, self.logger)
        return UserProfile(**json.loads(json_user_profile))
    
    def get_all_user_profiles(self) -> List[UserProfile]:
        path = f"/user-profiles"
        json_user_profiles, _ = make_request(self.base_uri, path, HttpMethod.GET, self.logger)
        return [UserProfile(**user_profile_dict) for user_profile_dict in json.loads(json_user_profiles)]
