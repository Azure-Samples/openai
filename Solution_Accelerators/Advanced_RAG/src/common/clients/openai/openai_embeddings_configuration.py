from typing import Optional

class OpenAIEmbeddingsConfiguration:
    def __init__(self,
                 content: Optional[str] = None,
                 embeddings_deployment_name: Optional[str] = None):
        if content is not None:
            self.content = content
        if embeddings_deployment_name is not None:
            self.embeddings_deployment_name = embeddings_deployment_name