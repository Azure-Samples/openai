class SearchSettings:
    def __init__(self, vectorization_enabled: bool):
        self.vectorization_enabled = vectorization_enabled

    def to_dict(self):
        return {
            "vectorization_enabled": self.vectorization_enabled
        }
