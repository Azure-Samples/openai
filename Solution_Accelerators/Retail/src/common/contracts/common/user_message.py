from typing import List

from pydantic import BaseModel

from common.contracts.common.user_prompt import PayloadType, UserPromptPayload

"""This class represents a single message from user. It stores user provided images as their URIs and text as string"""


class UserMessage(BaseModel, extra="allow"):
    payload: List[UserPromptPayload] = []
    role: str = "user"
    # additional_data: dict = {}
    # timestamp: AwareDatetime = dt.now(timezone.utc) # TODO: has issues with serialization throws error when sending via http post. commented out for now

    def add_text_payload(self, text: str):
        text_payload = UserPromptPayload(type="text", value=text)
        self.payload.append(text_payload)

    def add_img_uri_payload(self, sas_url: str):
        image_uri_payload = UserPromptPayload(type="image", value=sas_url)
        self.payload.append(image_uri_payload)

    def add_product_payload(self, product_id: str):
        product_payload = UserPromptPayload(type="product", value=product_id)
        self.payload.append(product_payload)

    def has_product_payload(self) -> bool:
        return any(item.type == "product" for item in self.payload)

    """Helper method to convert user message to string for passing as history to text based GPT models"""

    # TODO: should this go to extension class where this is implemented as an extension method?
    def get_user_message_str(self, dereference_product=False, product_descriptions=None) -> str:
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
            elif item.type == PayloadType.PRODUCT:
                if item.value is not None:
                    if dereference_product:
                        if item.value in product_descriptions:
                            if len(user_utterance) > 0:
                                user_utterance += ". <PRODUCT: " + product_descriptions[item.value] + ">"
                            else:
                                user_utterance = "<PRODUCT: " + product_descriptions[item.value] + ">"
                        else:
                            if len(user_utterance) > 0:
                                user_utterance += ". <PRODUCT-ID: " + item.value + ">"
                            else:
                                user_utterance = "<PRODUCT-ID: " + item.value + ">"
                    else:
                        if len(user_utterance) > 0:
                            user_utterance += ". <PRODUCT-ID: " + item.value + ">"
                        else:
                            user_utterance = "<PRODUCT-ID: " + item.value + ">"
        return user_utterance
