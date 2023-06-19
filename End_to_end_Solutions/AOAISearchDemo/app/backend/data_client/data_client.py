import copy
import json
import requests

from common.contracts.access_rule import AccessRule, Member, Resource
from common.contracts.chat_session import ChatSession, Dialog, DialogClassification, ParticipantType
from common.contracts.resource import ResourceProfile
from common.contracts.user_profile import UserProfile
from datetime import datetime
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Optional

from common.logging.log_helper import CustomLogger

class DataClient:
    class HttpMethod(Enum):
        POST="POST"
        GET="GET"
        PUT="PUT"
        DELETE="DELETE"

    def __init__(self, base_uri: str, logger: CustomLogger):
        self.base_uri = base_uri
        self.logger = logger
        
    def check_chat_session(self, user_id: str, conversation_id: str) -> bool:
        path = f"/check-chat-session/{user_id}/{conversation_id}"
        json_chat_session = self._make_request(path, self.HttpMethod.GET)

        if json_chat_session == 'true':
            return True
        else:
            return False

    def create_chat_session(self, user_id: str, conversation_id: str, initial_conversation: List[Dialog] = []) -> ChatSession:
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        initial_conversation_dct = [dialog.to_item() for dialog in initial_conversation]
        payload = {
            "initial_conversation": initial_conversation_dct
        }
        json_chat_session = self._make_request(path, self.HttpMethod.POST, payload)
        return ChatSession.as_payload(json_chat_session)

    def get_chat_session(self, user_id: str, conversation_id: str) -> ChatSession:
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        json_chat_session = self._make_request(path, self.HttpMethod.GET)
        return ChatSession.as_payload(json_chat_session)
    
    def add_dialog_to_chat_session(self, user_id: str, conversation_id: str, participant_type: ParticipantType, 
            timestamp: datetime, utterance: str, classification: DialogClassification) -> ChatSession:
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        payload = {
            "participant_type": participant_type.value,
            "timestamp": timestamp.isoformat(),
            "utterance": utterance,
            "classification": classification.value
        }
        json_chat_session = self._make_request(path, self.HttpMethod.PUT, payload)
        return ChatSession.as_payload(json_chat_session)
    
    def clear_chat_session(self, user_id: str, conversation_id: str):
        path = f"/chat-sessions/{user_id}/{conversation_id}"
        self._make_request(path, self.HttpMethod.DELETE)

    def create_user_profile(self, user_id: str, user_name: str, description: str) -> UserProfile:
        path = f"/user-profiles/{user_id}"
        payload = {
            "user_name": user_name,
            "description": description
        }
        json_user_profile = self._make_request(path, self.HttpMethod.POST, payload)
        return UserProfile.as_payload(json_user_profile)
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        path = f"/user-profiles/{user_id}"
        json_user_profile = self._make_request(path, self.HttpMethod.GET)
        return UserProfile.as_payload(json_user_profile)
    
    def get_all_user_profiles(self) -> List[UserProfile]:
        path = f"/user-profiles"
        json_user_profiles = self._make_request(path, self.HttpMethod.GET)
        return [UserProfile.as_item(json_user_profile) for json_user_profile in json.loads(json_user_profiles)]

    def filter_chat_session(self, chat_session: ChatSession, filter: DialogClassification):
        filtered_conversation = []
        for dialog in chat_session.conversation:
            if dialog.classification == filter:
                filtered_conversation.append(dialog)

        filtered_chat_session = copy.deepcopy(chat_session)
        filtered_chat_session.conversation = filtered_conversation
        return filtered_chat_session
    
    def create_access_rule(self, rule_id: str, resources: List[Resource], members: List[Member]) -> AccessRule:
        path = f"/access-rules/{rule_id}"
        payload = {
            "resources": resources,
            "members": members
        }
        json_user_profile = self._make_request(path, self.HttpMethod.POST, payload)
        return AccessRule.as_payload(json_user_profile)
    
    def get_access_rule(self, rule_id: str) -> AccessRule:
        path = f"/access-rules/{rule_id}"
        json_access_rule = self._make_request(path, self.HttpMethod.GET)
        return AccessRule.as_payload(json_access_rule)
    
    def get_user_resources(self, user_id: str) -> List[ResourceProfile]:
        path = f"/resources/user/{user_id}"
        json_resources = self._make_request(path, self.HttpMethod.GET)
        return [ResourceProfile.as_item(json_resource) for json_resource in json.loads(json_resources)]

    @retry(reraise=True, stop = stop_after_attempt(3), wait = wait_exponential(multiplier = 1, max = 60))
    def _make_request(self, path: str, method: HttpMethod, payload: Optional[dict] = None) -> str:

        headers = self.logger.get_converation_and_dialog_ids()
        properties = self.logger.get_updated_properties(headers)

        self.logger.info(f"Making {method.value} request to {path} endpoint", extra=properties)
        start_time = datetime.now()
        
        try:
            response: requests.Response
            if method == self.HttpMethod.POST:
                response = requests.post(url = self.base_uri + path, json = payload, headers=headers)
            elif method == self.HttpMethod.GET:
                response = requests.get(url = self.base_uri + path, json = payload, headers=headers)
            elif method == self.HttpMethod.PUT:
                response = requests.put(url = self.base_uri + path, json = payload, headers=headers)
            elif method == self.HttpMethod.DELETE:
                response = requests.delete(url = self.base_uri + path, json = payload, headers=headers)
            else:
                raise Exception(f"Invalid HTTP method: {method.value}")
            end_time = datetime.now()

            addl_dimension = {
                "sessionDB_request_time[MS]": (end_time - start_time).microseconds/1000
            }
            properties = self.logger.get_updated_properties(addl_dimension)

            response.raise_for_status()
            self.logger.info(f"Received response from {path} endpoint", extra=properties)
            return response.text
        except requests.RequestException as re:
            self.logger.error(f"Error making {method.value} request to {path} endpoint: {str(re)}", extra=properties)
            raise Exception(f"Error making {method.value} request to {path} endpoint: {str(re)}")