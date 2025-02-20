from copy import deepcopy
from enum import Enum
from common.telemetry.log_classes import LogProperties
from common.telemetry.log_helper import CustomLogger

class LogEvent(Enum):
    REQUEST_RECEIVED = "Request.Received"
    REQUEST_SUCCESS = "Request.Success"
    REQUEST_FAILED = "Request.Failed"


class AppLogger():
    def __init__(self, custom_logger: CustomLogger):
        self.custom_logger = custom_logger
        self.base_properties = {}
        self.max_log_length = 30000  # app insights has max log length of 32768 characters

    def set_base_properties(self, base_properties: dict | LogProperties):
        if isinstance(base_properties, LogProperties):
            self.base_properties = base_properties.model_dump()
        else:
            self.base_properties = base_properties

    def get_base_properties(self) -> dict:
        return deepcopy(self.base_properties)

    # update base properties
    def update_base_properties(self, base_properties: dict):
        self.base_properties.update(base_properties)

    def get_custom_logger(self) -> CustomLogger:
        return self.custom_logger

    def _merge_properties(self, properties):
        """
        Merges the base properties with the properties passed in and returns the merged properties.
        """
        if not properties:
            properties = {}

        # merge any base properties with the properties passed in
        all_properties = deepcopy(self.base_properties)
        custom_dimensions = {"custom_dimensions": {}}

        for key, value in all_properties.items():
            if isinstance(value, str) and len(value) > self.max_log_length:
                value = value[: self.max_log_length] + "<<TRUNCATED>>"
            custom_dimensions["custom_dimensions"][key] = value

        for key, value in properties.items():
            if isinstance(value, str) and len(value) > self.max_log_length:
                value = value[: self.max_log_length] + "<<TRUNCATED>>"
            custom_dimensions["custom_dimensions"][key] = value

        return custom_dimensions
    
    def info(self, msg: str, event: LogEvent = None, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        if properties is None:
            properties = {}
        if event:
            properties["event"] = f"{event.value}"
        all_properties = self._merge_properties(properties)
        if len(msg) > self.max_log_length:
            msg = msg[: self.max_log_length] + "<<TRUNCATED>>"
        self.custom_logger.info(msg, extra=all_properties)

    def debug(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        all_properties = self._merge_properties(properties)
        self.custom_logger.info(msg, extra=all_properties)

    def warning(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        all_properties = self._merge_properties(properties)
        self.custom_logger.warning(msg, extra=all_properties)

    def error(self, msg: str, event: LogEvent = None, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        if properties is None:
            properties = {}
        if event:
            properties["event"] = f"{event.value}"
        all_properties = self._merge_properties(properties)
        self.custom_logger.error(msg, extra=all_properties)

    def exception(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        all_properties = self._merge_properties(properties)
        self.custom_logger.exception(msg, extra=all_properties)

    def critical(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        all_properties = self._merge_properties(properties)
        self.custom_logger.critical(msg, extra=all_properties)
    
    def log_request_received(self, msg: str, properties: LogProperties = None):
        properties = self._update_properties(properties)
        self.info(msg, LogEvent.REQUEST_RECEIVED, properties)
    
    def log_request_success(self, msg: str, properties: LogProperties = None):
        properties = self._update_properties(properties)
        self.info(msg, LogEvent.REQUEST_SUCCESS, properties)
    
    def log_request_failed(self, msg: str, properties: LogProperties = None):
        properties = self._update_properties(properties)
        self.error(msg, LogEvent.REQUEST_FAILED, properties)
    
    def _update_properties(self, properties: LogProperties = None):
        if not properties:
            properties = LogProperties()
        if properties:
            properties.set_start_time()
            properties = properties.model_dump()
        return properties
    
