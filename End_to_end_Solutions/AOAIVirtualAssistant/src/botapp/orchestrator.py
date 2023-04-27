# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from data.chat_sessions.contracts.chat_session import DialogClassification
from data.chat_sessions.contracts.chat_session import ParticipantType
from tasks.chit_chat import ChitChat
from tasks.topic_classifier import TopicClassifier
from tasks.auto_insurance import AutoInsurance
from tasks.end_conversation import EndConversation
from tasks.flood_insurance import FloodInsurance
from data.model_classes import ModelClasses
from data.chat_sessions.api.manager import ChatSessionManager
from datetime import datetime

class Orchestrator:
    def __init__(self):
        self.chat_sessions_manager = ChatSessionManager('aoai-va-cosmos-db', 'chat_sessions')
        self.chit_chat = ChitChat()
        self.auto_insurance = AutoInsurance()
        self.flood_insurance = FloodInsurance()
        self.topic_classifier = TopicClassifier()

    def get_or_create_conversation(self, conversation_id: str):
        """
        Retrives current session from DB, if not present creates new session.

        Args:
            utterance (str): query
            session_id (str): unique session id used to identify user/interface_client
            user_id (str): user profile name, example: emma

        Returns:
            None
        """
        conversation = self.chat_sessions_manager.get_chat_session(conversation_id)
        if conversation == None:
            self.chat_sessions_manager.create_chat_session(conversation_id)
        
        conversation = self.chat_sessions_manager.get_chat_session(conversation_id)

        return conversation

    def run_query(self, conversation, user_id, conversation_id, query) -> dict:
        """
        Classifies User Query and runs corresponding model

        Returns:
            dict: model response for the input query.
        """
        classification = self.topic_classifier.run(query)

        if classification == ModelClasses.CONTINUATION.value:
            if len(conversation.conversation) > 0:
                classification = self.chat_sessions_manager.dialog_classification_to_model_classes(getattr(conversation.conversation[-1],"classification", ModelClasses.CHIT_CHAT.value))
            else:
                classification = ModelClasses.CHIT_CHAT.value

        self.chat_sessions_manager.add_dialog_to_chat_session(conversation_id, 
                                                              user_id, ParticipantType.user, 
                                                              datetime.now(), 
                                                              query, 
                                                              self.chat_sessions_manager.model_classes_to_dialog_classification(classification))

        conversation = self.chat_sessions_manager.get_chat_session(conversation_id)

        agent_response = ""

        if classification == ModelClasses.AUTO_INSURANCE.value:
            agent_response = self.auto_insurance.run(conversation, user_id)

        elif classification == ModelClasses.HOME_FLOOD_INSURANCE.value:
            agent_response = self.flood_insurance.run(conversation, user_id)
        else:
            agent_response = self.chit_chat.run(conversation, user_id)

        self.chat_sessions_manager.add_dialog_to_chat_session(conversation_id, 
                                                              "bot", 
                                                              ParticipantType.assistant, 
                                                              datetime.now(), 
                                                              agent_response, 
                                                              self.chat_sessions_manager.model_classes_to_dialog_classification(classification))

        return {"response": agent_response}