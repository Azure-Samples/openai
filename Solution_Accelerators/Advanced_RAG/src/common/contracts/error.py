#TODO: These are not used anywhere in the code. Remove them if not needed.

class OutOfScopeException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class UnauthorizedDBAccessException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message