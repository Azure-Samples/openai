import os
from prefect import Task
from cognition.openai.model_manager import OpenAIModelManager
from data.conversation_store import ConversationStore
from utilities.model_input_convertor import ModelInputConvertor
from config import DefaultConfig


class EndConversation(Task):
    def __init__(self, conversation_store: ConversationStore, **kwargs):
        self.conversation_store = conversation_store
        super().__init__(**kwargs)

    def run(self):
        transcript_summarizer = OpenAIModelManager(os.path.join(os.getcwd(), 'cognition', 'config.yml'),
                                                   'transcript-summary', {'api-key': DefaultConfig.OPENAI_RESOURCE_KEY})
        #
        # Todo: Update data fetch post cosmos integration and remove in-memory data store/retrieval above.
        #
        return transcript_summarizer.generate_dialog({"<CONTEXT>": ModelInputConvertor.model_input_convertor(self.conversation_store.get_transcript())})
