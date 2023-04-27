import os

from data.chat_sessions.contracts.chat_session import DialogClassification
from data.chat_sessions.contracts.chat_session import ChatSession
from data.faqs.contracts.faq import InsuranceType
from cognition.openai.model_manager import OpenAIModelManager
from utilities.model_input_convertor import ModelInputConvertor
from data.user_profiles.api.manager_flat import UserProfileManagerFlat
from data.faqs.api.manager import FAQManager
from config import DefaultConfig


class FloodInsurance:
    def __init__(self, **kwargs):
        self.database_name = DefaultConfig.COSMOS_DB_NAME
        self.user_profile_container_name = DefaultConfig.COSMOS_DB_USER_PROFILE_CONTAINER_NAME
        self.faq_container_name = DefaultConfig.COSMOS_DB_FAQ_CONTAINER_NAME
        self.name = "flood-insurance"

        self.user_profile_manager = UserProfileManagerFlat(self.database_name, self.user_profile_container_name)
        self.faq_manager = FAQManager(self.database_name, self.faq_container_name)
        

    def run(self, conversation: ChatSession, user_id: str):

        open_ai_config = {'api-key': DefaultConfig.OPENAI_RESOURCE_KEY,
                          'resource-name': DefaultConfig.OPENAI_RESOURCE_NAME,
                          'deployment-name': DefaultConfig.OPENAI_CHATGPT_DEPLOYMENT_NAME,
                          'api-version': DefaultConfig.OPENAI_API_VERSION
                          }
        config_file_path = os.path.join(os.getcwd(), 'cognition', 'config.yml')
        flood_insurance_model = OpenAIModelManager(config_file_path, self.name, open_ai_config)

        filtered_transcript = conversation.get_transcript({'classification': DialogClassification.flood_insurance.value})
        model_converted_transcript = ModelInputConvertor.model_input_convertor(filtered_transcript)

        relevant_info = self.faq_manager.get_faqs(InsuranceType.flood).info.relevant_info
        aux_info = self.faq_manager.get_faqs(InsuranceType.flood).info.aux_info
        user_info = self.user_profile_manager.get_user_profile(user_id).__str__()

        return flood_insurance_model.generate_dialog({"<CONTEXT>": model_converted_transcript,
                                                     "<CONTENT_A>": user_info,
                                                     "<CONTENT_B>": relevant_info,
                                                     "<CONTENT_C>": aux_info})
