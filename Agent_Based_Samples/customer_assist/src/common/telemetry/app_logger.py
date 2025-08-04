# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import logging
from enum import Enum
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource, ResourceAttributes
from opentelemetry._logs import set_logger_provider


from common.telemetry.log_classes import LogProperties

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "telemetry"})

class LogEvent(Enum):
    REQUEST_RECEIVED = "Request.Received"
    REQUEST_SUCCESS = "Request.Success"
    REQUEST_FAILED = "Request.Failed"

class ConsoleLogFilter(logging.Filter):
    '''
    Since we are using root logger, in console we see all the logs from all the modules.
    This filter will filter out logs that are not from the semantic kernel module or our app.
    '''
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.abspath(os.path.join(__file__, "..", ".."))
    
    def filter(self, record):
        if os.path.abspath(record.pathname).startswith(self.base_dir):
            return True
        
        return record.name.startswith("semantic_kernel")

class AppLogger:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger_provider = LoggerProvider(resource)

        self.initialize_loggers()
        
    def initialize_loggers(self):
        if self.connection_string:
            if not any(
                isinstance(handler, LoggingHandler)
                for handler in self.logger.handlers
            ):
                self.azure_exporter = AzureMonitorLogExporter(connection_string=self.connection_string)
                self.logger_provider.add_log_record_processor(BatchLogRecordProcessor(self.azure_exporter))
                self.handler = LoggingHandler()
                self.logger.addHandler(self.handler)

        # add console logger if it is not already added by another instance of CustomLogger
        if not any(
            isinstance(handler, logging.StreamHandler)
            for handler in self.logger.handlers
        ):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.addFilter(ConsoleLogFilter())
            self.logger.addHandler(console_handler)
        set_logger_provider(self.logger_provider)

    def info(self, message:str, properties: dict = None):
        self.logger.info(message)

    # Put this function for now, but if we decide to go with this approach, we can delete this function
    # TODO: Remove set_base_properties function here and through code.
    def set_base_properties(self, base_properties: dict | LogProperties):
        pass

    def debug(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.info(msg)

    def warning(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.warning(msg)

    def error(self, msg: str, event: LogEvent = None, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.error(msg)

    def exception(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.exception(msg)

    def critical(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.critical(msg)

    def log_request_received(self, msg: str, properties: LogProperties = None):
        self.info(msg)

    def log_request_success(self, msg: str, properties: LogProperties = None):
        self.info(msg)

    def log_request_failed(self, msg: str, properties: LogProperties = None):
        self.error(msg)