class ClientAuthenticationException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class InvalidArgumentException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ImageAnalysisException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
