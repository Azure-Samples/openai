class InvalidConfigError(Exception):
    def __init__(self, message="Config error occurred."):
        self.message = message
        super().__init__(self.message)


class VectorSearchError(Exception):
    def __init__(self, message="Vector Search Error occurred."):
        self.message = message
        super().__init__(self.message)


class SearchIndexError(Exception):
    def __init__(self, message="Search Index Error occurred."):
        self.message = message
        super().__init__(self.message)


class MissingCognitiveSearchIndexError(Exception):
    def __init__(self, message="Index error occurred."):
        self.message = message
        super().__init__(self.message)
