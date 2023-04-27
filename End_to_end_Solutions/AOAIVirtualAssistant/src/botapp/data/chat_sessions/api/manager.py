import datetime
from typing import List, Optional
from data.model_classes import ModelClasses
from data.chat_sessions.contracts.chat_session import ChatSession, Dialog, DialogClassification, ParticipantType
from data.cosmosdb.api.container import CosmosDBContainer
from data.cosmosdb.utilities.property_item_reader import read_item_property_with_type, read_item_property_with_enum

"""
Manager API for creating, retrieving and updating chat sessions in storage.
"""
class ChatSessionManager:
    PARTITION_KEY_NAME = "conversation_id"
    UNIQUE_KEYS = [
        {'paths': ['/conversation_id']}
    ]

    def __init__(self, database_name: str, container_name: str):
        self.container = CosmosDBContainer(database_name, container_name, self.PARTITION_KEY_NAME, self.UNIQUE_KEYS)
    
    """
    Creates a new chat session with the specified conversation ID and optional initial conversation.
    """
    def create_chat_session(self, converation_id: str, initial_conversation: List[Dialog] = []):
        chat_session = ChatSession(converation_id, initial_conversation)
        self.container.create_item(converation_id, chat_session.to_item())

    """
    Retrieves and deserializes a chat session using the specified conversation ID.
    Returns None if no chat session witht with the specified conversation ID exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_chat_session(self, conversation_id: str) -> Optional[ChatSession]:
        item = self.container.get_item(conversation_id)
        if item is None:
            return None
        
        conversationDict = read_item_property_with_type(item, "conversation", list, ChatSession)
        conversation = []
        for dialogDict in conversationDict:
            participant_name = read_item_property_with_type(dialogDict, "participant_name", str, Dialog)
            valid_participant_types = [type.value for type in ParticipantType]
            participant_type = read_item_property_with_enum(dialogDict, "participant_type", valid_participant_types, ParticipantType, Dialog)
            utterance = read_item_property_with_type(dialogDict, "utterance", str, Dialog)
            timestamp = read_item_property_with_type(dialogDict, "timestamp", datetime.datetime, Dialog, datetime.datetime.fromisoformat)
            valid_classification_types = [type.value for type in DialogClassification]
            classification = read_item_property_with_enum(dialogDict, "classification", valid_classification_types, DialogClassification, Dialog)
            dialog = Dialog(participant_name, participant_type, utterance, timestamp, classification)
            conversation.append(dialog)
        
        return ChatSession(conversation_id, conversation)
    
    """
    Clears the chat session with the specified conversation ID.
    Raises an exception if no chat session exists with the specified conversation ID.
    """
    def clear_chat_session(self, conversation_id: str):
        chat_session = self.get_chat_session(conversation_id)
        if chat_session is None:
            raise Exception("Chat session with conversation ID " + conversation_id + " could not be found.")
        
        chat_session.clear_conversation()
        self.container.update_item(conversation_id, chat_session.to_item())

    """
    Adds a new dialog to the chat session with the specified conversation ID.
    Raises an exception if no chat session exists with the specified conversation ID.
    """
    def add_dialog_to_chat_session(self, conversation_id: str, participant_name: str, participant_type: ParticipantType, 
            timestamp: datetime.datetime, utterance: str, classification: DialogClassification):
        dialog = Dialog(participant_name, participant_type, utterance, timestamp, classification)
        chat_session = self.get_chat_session(conversation_id)
        if chat_session is None:
            raise Exception("Chat session with conversation ID " + conversation_id + " could not be found.")
        
        chat_session.add_dialog(dialog)
        self.container.update_item(conversation_id, chat_session.to_item())

    
    def model_classes_to_dialog_classification(self, classification: str):
        if classification == ModelClasses.CHIT_CHAT.value:
            return DialogClassification.chit_chat
        elif classification == ModelClasses.AUTO_INSURANCE.value:
            return DialogClassification.auto_insurance
        elif classification == ModelClasses.HOME_FLOOD_INSURANCE.value:
            return DialogClassification.flood_insurance
        elif classification == ModelClasses.ENDING_CONVERSATION.value:
            return DialogClassification.end_conversation
        else:
            return DialogClassification.chit_chat
        
    def dialog_classification_to_model_classes(self, dialog_classification: str):
        if dialog_classification == DialogClassification.chit_chat:
            return ModelClasses.CHIT_CHAT.value
        elif dialog_classification == DialogClassification.auto_insurance:
            return ModelClasses.AUTO_INSURANCE.value
        elif dialog_classification == DialogClassification.flood_insurance:
            return ModelClasses.HOME_FLOOD_INSURANCE.value
        elif dialog_classification == DialogClassification.end_conversation:
            return ModelClasses.ENDING_CONVERSATION.value
        else:
            return ModelClasses.CHIT_CHAT.value