from enum import Enum
from quart import jsonify

from common.telemetry.log_classes import LogProperties
from common.telemetry.app_logger import AppLogger

class HTTPStatusCode(Enum):
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNSUPPORTED_MEDIA_TYPE = 415
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503

def create_error_response(status_code: HTTPStatusCode, message: str, log_properties: LogProperties = None, logger: AppLogger = None):
    if logger:
        logger.log_request_failed(message, properties=log_properties)
    return jsonify({"error": message}), status_code.value