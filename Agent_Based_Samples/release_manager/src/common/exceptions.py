# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

class ContentFilterException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 403


class RateLimitException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 429


class ServiceUnavailableException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 503


class FileDownloadError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 400


class FileProcessingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 400


class CacheKeyExistsError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 500


class CacheKeyNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 404


class MessageProcessingTimeoutError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 500


class ClientConnectionClosedException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 400
