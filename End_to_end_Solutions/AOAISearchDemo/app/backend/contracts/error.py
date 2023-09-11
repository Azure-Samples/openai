from backend.contracts.chat_response import ApproachType

class OutOfScopeException(Exception):
    def __init__(self, message, suggested_classification: ApproachType):
        super().__init__(message)
        self.message = message
        self.suggested_classification = suggested_classification
    
class UnauthorizedDBAccessException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ContentFilterException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message