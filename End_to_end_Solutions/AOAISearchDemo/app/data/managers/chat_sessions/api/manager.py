from azure.cosmos import CosmosClient
from common.contracts.chat_session import ChatSession, Dialog, DialogClassification, ParticipantType
from data.cosmosdb.container import CosmosDBContainer, CosmosConflictError
from datetime import datetime
from typing import Any, List, Optional

class SessionNotFoundError(BaseException):
    pass

"""
Manager API for creating, retrieving and updating chat sessions in storage.
"""
class ChatSessionManager:
    PARTITION_KEY_NAME = "partition_key"
    UNIQUE_KEYS = [
        {"paths": [f"/{PARTITION_KEY_NAME}"]}
    ]

    def __init__(self, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_chat_sessions_container_name: str):
        cosmos_client = CosmosClient(url=cosmos_db_endpoint, credential=cosmos_db_credential, consistency_level="Session")
        self.container = CosmosDBContainer(cosmos_db_name, cosmos_db_chat_sessions_container_name, self.PARTITION_KEY_NAME, cosmos_client, self.UNIQUE_KEYS)
    
    """
    Creates a new chat session with the specified conversation ID and optional initial conversation.
    """
    def create_chat_session(self, user_id: str, conversation_id: str, initial_conversation: List[Dialog] = []) -> ChatSession:
        chat_session = ChatSession(user_id, conversation_id, initial_conversation)
        try:
            item = chat_session.to_item()
            partition_key = f"{user_id}|{conversation_id}"
            created_item = self.container.create_item(conversation_id, partition_key, item)
            return ChatSession.as_item(created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"Chat session with conversation ID {conversation_id} already exists.")        

    """
    Retrieves and deserializes a chat session using the specified conversation ID.
    Returns None if no chat session witht with the specified conversation ID exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_chat_session(self, user_id: str, conversation_id: str) -> Optional[ChatSession]:
        item = self.container.get_item(conversation_id, f"{user_id}|{conversation_id}")
        if item is None:
            return None
        
        return ChatSession.as_item(item)
    
    """
    Clears the chat session with the specified conversation ID.
    Raises an exception if no chat session exists with the specified conversation ID.
    """
    def clear_chat_session(self, user_id: str, conversation_id: str):
        chat_session = self.get_chat_session(user_id, conversation_id)
        if chat_session is None:
            raise SessionNotFoundError(f"Chat session with conversation ID {conversation_id} could not be found.")
        
        chat_session.clear_conversation()
        item = chat_session.to_item()
        partition_key = f"{user_id}|{conversation_id}"
        self.container.update_item(conversation_id, partition_key, item)

    """
    Adds a new dialog to the chat session with the specified conversation ID.
    Raises an exception if no chat session exists with the specified conversation ID.
    """
    def add_dialog_to_chat_session(self, user_id: str, conversation_id: str, participant_type: ParticipantType, 
            timestamp: datetime, utterance: str, classification: DialogClassification) -> ChatSession:
        dialog = Dialog(participant_type, utterance, timestamp, classification)
        chat_session = self.get_chat_session(user_id, conversation_id)
        if chat_session is None:
            raise SessionNotFoundError(f"Chat session with conversation ID {conversation_id} could not be found.")
        chat_session.add_dialog(dialog)
        item = chat_session.to_item()
        partition_key = f"{user_id}|{conversation_id}"
        updated_item = self.container.update_item(conversation_id, partition_key, item)
        return ChatSession.as_item(updated_item)