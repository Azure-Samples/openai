import os
from prefect import Task
from cognition.openai.model_manager import OpenAIModelManager
from config import DefaultConfig


class TopicClassifier(Task):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "topic-classifier"

    def run(self, query) -> str:
        open_ai_config = {'api-key': DefaultConfig.OPENAI_RESOURCE_KEY,
                          'resource-name': DefaultConfig.OPENAI_RESOURCE_NAME,
                          'deployment-name': DefaultConfig.OPENAI_GPT_DEPLOYMENT_NAME,
                          'api-version': DefaultConfig.OPENAI_API_VERSION
                          }
        config_file_path = os.path.join(os.getcwd(), 'cognition', 'config.yml')
        
        topic_classifier = OpenAIModelManager(config_file_path, self.name, open_ai_config)

        classifier_payload = {"<CONTEXT>": query}
        
        response = topic_classifier.generate_dialog(classifier_payload)

        return response.replace("Classified topic:", "").replace('"', "").strip().lower()
