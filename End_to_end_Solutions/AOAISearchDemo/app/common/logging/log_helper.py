import logging
from copy import deepcopy
from opencensus.ext.azure.log_exporter import AzureLogHandler

class CustomLogger(logging.LoggerAdapter):
    def __init__(self, app_insights_cnx_str):
        self.app_insights_cnx_str = app_insights_cnx_str
        self.extra = {}
        
        custom_dimensions = {
            "conversation_id": "please set conversation_id before logging",
            "dialog_id": "please set dialog_id before logging"
        }

        log_properties = {
            "custom_dimensions": custom_dimensions,
        }
        self.extra = log_properties

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        self.initialize_loggers()
    
    def set_conversation_id(self, conversation_id: str):
        self.extra["custom_dimensions"]["conversation_id"] = conversation_id
    
    def set_dialog_id(self, dialog_id: str):
        self.extra["custom_dimensions"]["dialog_id"] = dialog_id
    
    def set_conversation_and_dialog_ids(self, conversation_id: str, dialog_id: str):
        self.set_conversation_id(conversation_id)
        self.set_dialog_id(dialog_id)
    
    def get_converation_and_dialog_ids(self) -> dict:
        return {
            "conversation_id": self.extra["custom_dimensions"]["conversation_id"],
            "dialog_id": self.extra["custom_dimensions"]["dialog_id"]
        }
    
    def initialize_loggers(self):
        if self.app_insights_cnx_str:

            # add appInsights logger if it is not already added by another instance of CustomLogger
            if not any(isinstance(handler, AzureLogHandler) for handler in self.logger.handlers):
                az_log_handler = AzureLogHandler(connection_string=self.app_insights_cnx_str)
                self.logger.addHandler(az_log_handler)

        # add console logger if it is not already added by another instance of CustomLogger
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)

            self.logger.addHandler(console_handler)

    def process(self, msg, kwargs):
        """
        Extract conversation_id and include it in the log message
        """
        extra = kwargs.get("extra") or self.extra
        if extra.__contains__("custom_dimensions"):
            custom_dimensions = extra["custom_dimensions"]
            conversation_id = custom_dimensions["conversation_id"]
        else:
             conversation_id = "Conversation_id NOT SET while logging"
        
        # include all properties except custom dimensions in extra dictionary to message 
        for key, value in extra.items():
            if key != "custom_dimensions":
                msg = msg + f", {key}: {value}"
        return 'Conversation_id: %s, %s' % (conversation_id, msg), kwargs
    
    def get_updated_properties(self, additional_custom_dimensions: dict, additional_properties: dict = {} ) -> dict:
        """
        Add custom dimensions to the logger
        """
        custom_dimensions = self.get_updated_custom_dimensions(additional_custom_dimensions)

        properties = deepcopy(self.extra)

        for key, value in additional_properties.items():
            if key != "custom_dimensions":
                properties[key] = value
        properties["custom_dimensions"] = custom_dimensions

        return properties
    
    def get_updated_custom_dimensions(self, additional_custom_dimensions: dict) -> dict:
        """
        Add custom dimensions to the logger
        """
        dimensions = deepcopy(self.extra["custom_dimensions"])
        for key, value in additional_custom_dimensions.items():
            dimensions[key] = value

        return dimensions