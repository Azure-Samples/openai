# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from copy import deepcopy
from opencensus.ext.azure.log_exporter import AzureLogHandler


class CustomLogger(logging.LoggerAdapter):
    def __init__(self, app_insights_cnx_str):
        self.app_insights_cnx_str = app_insights_cnx_str

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.initialize_loggers()

    def initialize_loggers(self):
        if self.app_insights_cnx_str:

            # add appInsights logger if it is not already added by another instance of CustomLogger
            if not any(
                isinstance(handler, AzureLogHandler) for handler in self.logger.handlers
            ):
                az_log_handler = AzureLogHandler(
                    connection_string=self.app_insights_cnx_str
                )
                self.logger.addHandler(az_log_handler)

        # add console logger if it is not already added by another instance of CustomLogger
        if not any(
            isinstance(handler, logging.StreamHandler)
            for handler in self.logger.handlers
        ):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(console_handler)

    def process(self, msg, kwargs):
        """
        Extract conversation_id and include it in the log message
        """
        extra = kwargs.get("extra")
        if extra.__contains__("custom_dimensions"):
            custom_dimensions = extra["custom_dimensions"]
            conversation_id = custom_dimensions.get(
                "conversation_id", "Conversation_id NOT SET while logging"
            )
        else:
            conversation_id = "Conversation_id NOT SET while logging"

        # include all properties except custom dimensions in extra dictionary to message
        for key, value in extra.items():
            if key != "custom_dimensions":
                msg = msg + f", {key}: {value}"
        return "%s. Conversation_id: %s" % (msg, conversation_id), kwargs
