# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

from common.contracts.common.user_query import PayloadType, UserQueryPayload


class UserMessage:
    def __init__(self):
        self.payload: List[UserQueryPayload] = []
        self.role: str = "user"

    def add_text_payload(self, text: str):
        text_payload = UserQueryPayload(type="text", value=text)
        self.payload.append(text_payload)

    def add_img_uri_payload(self, sas_url: str):
        image_uri_payload = UserQueryPayload(type="image", value=sas_url)
        self.payload.append(image_uri_payload)

    def get_user_message_str(self) -> str:
        """
        Helper method to convert user message to string for passing as history to text based GPT models.
        """
        user_utterance = ""
        for item in self.payload:
            if item.type == PayloadType.IMAGE:
                if len(user_utterance) > 0:
                    user_utterance += ". <IMAGE-URI: " + item.value + ">"
                else:
                    user_utterance += ". <IMAGE-URI: " + item.value + ">"
            elif item.type == PayloadType.TEXT:
                if item.value is not None:
                    if len(user_utterance) > 0:
                        user_utterance += ". " + item.value
                    else:
                        user_utterance = item.value
        return user_utterance
