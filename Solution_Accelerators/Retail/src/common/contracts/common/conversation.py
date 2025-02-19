from pydantic import BaseModel
from common.contracts.common.user_message import UserMessage
from common.contracts.common.bot_message import BotMessage
from typing import List, Optional
from copy import deepcopy

"""This class represents a single dialog between user and bot"""
class Dialog(BaseModel):
    user_message: Optional[UserMessage] = None
    bot_message: Optional[BotMessage] = None

    def add_user_message(self, user_message: UserMessage):
        self.user_message = user_message

    def add_bot_message(self, bot_message: BotMessage):
        self.bot_message = bot_message

"""This class represents user / bot message as a flattened string to be used with text based GPT models"""
class TextHistory(BaseModel):
    role: str
    content: str

"""This class represents a conversation between user and bot. It contains a list of dialogs between user and bot"""
class Conversation(BaseModel):
    dialogs: List[Dialog] = []

    def add_dialog(self, dialog: Dialog):
        self.dialogs.append(dialog)

    """Helper method to convert conversation to string for passing as history to text based GPT models"""
    # TODO: should this go to extension class where this is implemented as an extension method?
    def generate_text_history(self, filter_by=None, last_n = None) -> List[TextHistory]:
        if filter_by is None:
            filter_by = dict()
        history = []

        all_dialogs = deepcopy(self.dialogs)
        filtered_dialogs = all_dialogs

        for key, value in filter_by.items():
            filtered_dialogs = list(filter(lambda x: getattr(x, key).value == value, filtered_dialogs))

        # return all if last_n is None, else return last n
        dialogs_to_return = filtered_dialogs if last_n is None else filtered_dialogs[-last_n:]

        for dialog in dialogs_to_return:
            if dialog.user_message :
                history.append(TextHistory(role=dialog.user_message.role, content=dialog.user_message.get_user_message_str()))
            if dialog.bot_message:
                history.append(TextHistory(role=dialog.bot_message.role, content=dialog.bot_message.get_bot_response_str()))
        return history