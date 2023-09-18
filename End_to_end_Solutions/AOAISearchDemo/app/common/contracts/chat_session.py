import json
from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import Iterable, List

from common.utilities.property_item_reader import (
    MissingPropertyError,
    read_item_property_with_enum,
    read_item_property_with_type,
)


class ParticipantType(Enum):
    user = "user"
    assistant = "assistant"


class DialogClassification(Enum):
    chit_chat = "chit_chat"
    structured_query = "structured_query"
    unstructured_query = "unstructured_query"
    continuation = "continuation"
    inappropiate = "inappropiate"


"""
Object representing a piece of dialog in a chat session between a user and the bot assistant.
"""


class Dialog:
    def __init__(
        self,
        participant_type: ParticipantType,
        utterance: str,
        timestamp: datetime,
        classification: DialogClassification,
    ):
        self.participant_type = participant_type
        self.utterance = utterance
        self.timestamp = timestamp
        self.classification = classification

    def to_item(self):
        return {
            "participant_type": self.participant_type.value,
            "utterance": self.utterance,
            "timestamp": self.timestamp.isoformat(),
            "classification": self.classification.value,
        }

    @staticmethod
    def as_item(dct: dict):
        valid_participant_types = [type.value for type in ParticipantType]
        participant_type = read_item_property_with_enum(
            dct, "participant_type", valid_participant_types, ParticipantType, Dialog
        )
        utterance = read_item_property_with_type(dct, "utterance", str, Dialog)
        timestamp = read_item_property_with_type(
            dct, "timestamp", datetime, Dialog, datetime.fromisoformat
        )
        valid_classification_types = [type.value for type in DialogClassification]
        classification = read_item_property_with_enum(
            dct,
            "classification",
            valid_classification_types,
            DialogClassification,
            Dialog,
        )
        return Dialog(participant_type, utterance, timestamp, classification)


"""
Object representing a chat session between a user and the bot assistant.
"""


class ChatSession:
    def __init__(
        self, user_id: str, conversation_id: str, conversation: List[Dialog] = []
    ):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.conversation = conversation

    def add_dialog(self, dialog: Dialog):
        self.conversation.append(dialog)

    def clear_conversation(self):
        self.conversation = []

    def to_item(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "conversation": [dialog.to_item() for dialog in self.conversation],
        }

    def get_transcript(self, filter_by=None):
        if filter_by is None:
            filter_by = dict()

        filtered_transcript = deepcopy(self.conversation)

        for key, value in filter_by.items():
            filtered_transcript = list(
                filter(lambda x: getattr(x, key).value == value, filtered_transcript)
            )

        return filtered_transcript

    @staticmethod
    def as_item(dct: dict):
        user_id = read_item_property_with_type(dct, "user_id", str, ChatSession)
        conversation_id = read_item_property_with_type(
            dct, "conversation_id", str, ChatSession
        )
        conversation_dict = read_item_property_with_type(
            dct, "conversation", list, ChatSession
        )

        conversation: List[Dialog] = []
        for dialog_dict in conversation_dict:
            conversation.append(Dialog.as_item(dialog_dict))

        return ChatSession(user_id, conversation_id, conversation)

    @staticmethod
    def as_payload(payload: str):
        dct = json.loads(payload)

        try:
            return ChatSession.as_item(dct)
        except MissingPropertyError:
            raise Exception(f"Invalid ChatSession payload.")
