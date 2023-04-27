import os
from data.chat_sessions.contracts.chat_session import DialogClassification

from cognition.openai.model_manager import OpenAIModelManager
from config import DefaultConfig
from data.chat_sessions.contracts.chat_session import ChatSession
from data.user_profiles.api.manager_flat import UserProfileManagerFlat
from utilities.model_input_convertor import ModelInputConvertor


class ChitChat:
    def __init__(self, **kwargs):
        self.database_name = DefaultConfig.COSMOS_DB_NAME
        self.user_profile_container_name = DefaultConfig.COSMOS_DB_USER_PROFILE_CONTAINER_NAME
        self.user_profile_manager_flat = UserProfileManagerFlat(self.database_name, self.user_profile_container_name)
        self.name = "chit-chat"

    def run(self, conversation: ChatSession, user_id: str) -> str:

        open_ai_config = {'api-key': DefaultConfig.OPENAI_RESOURCE_KEY,
                          'resource-name': DefaultConfig.OPENAI_RESOURCE_NAME,
                          'deployment-name': DefaultConfig.OPENAI_CHATGPT_DEPLOYMENT_NAME,
                          'api-version': DefaultConfig.OPENAI_API_VERSION
                          }
        config_file_path = os.path.join(os.getcwd(), 'cognition', 'config.yml')
        chit_chat_model = OpenAIModelManager(config_file_path, self.name, open_ai_config)

        full_transcript = conversation.get_transcript()
        model_converted_transcript = ModelInputConvertor.model_input_convertor(full_transcript)

        user_info = self.user_profile_manager_flat.get_user_profile(user_id).__str__()

        return chit_chat_model.generate_dialog({"<CONTEXT>": model_converted_transcript,
                                                "<CONTENT_A>": user_info})
