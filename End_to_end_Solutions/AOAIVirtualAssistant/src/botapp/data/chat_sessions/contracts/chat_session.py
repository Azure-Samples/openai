import datetime
from enum import Enum
from typing import List
from copy import deepcopy

class ParticipantType(Enum):
    user = "user"
    assistant = "assistant"

class DialogClassification(Enum):
    chit_chat = "chit_chat"
    auto_insurance = "auto_insurance"
    flood_insurance = "flood_insurance"
    end_conversation = "end_conversation"

"""
Object representing a piece of dialog in a chat session between a user and the bot assistant.
"""
class Dialog:
    def __init__(self, participant_name: str, participant_type: ParticipantType, utterance: str, timestamp: datetime.datetime, classification: DialogClassification):
        self.participant_name = participant_name
        self.participant_type = participant_type
        self.utterance = utterance
        self.timestamp = timestamp
        self.classification = classification

    def to_item(self):
        return {
            "participant_name": self.participant_name,
            "participant_type": self.participant_type.value,
            "utterance": self.utterance,
            "timestamp": self.timestamp.isoformat(),
            "classification": self.classification.value
        }

"""
Object representing a chat session between a user and the bot assistant.
"""
class ChatSession:
    def __init__(self, conversation_id: str, conversation: List[Dialog] = []):
        self.conversation_id = conversation_id
        self.conversation = conversation

    def add_dialog(self, dialog: Dialog):
        self.conversation.append(dialog)
    
    def clear_conversation(self):
        self.conversation = []

    def to_item(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "conversation": [dialog.to_item() for dialog in self.conversation]
        }

    def get_transcript(self, filter_by=None):
        if filter_by is None:
            filter_by = dict()

        filtered_transcript = deepcopy(self.conversation)

        for key, value in filter_by.items():
            filtered_transcript = list(filter(lambda x: getattr(x, key).value == value, filtered_transcript))

        return filtered_transcript