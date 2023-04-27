#
# Todo: can mostly be removed post integration with cosmos.
#
from data.dialog_turn import DialogTurn
from copy import deepcopy


class ConversationStore:
    def __init__(self, **kwargs):
        self.dialog_turn_messages = kwargs.get("dialog_turn_messages", list())

    def add_message(self, message):
        self.dialog_turn_messages.append(deepcopy(message))

    def update_message_data(self, updated_message, pos=-1):
        if isinstance(updated_message, DialogTurn):
            _ = self.dialog_turn_messages.pop(pos)
            self.dialog_turn_messages.append(deepcopy(updated_message))

    def get_transcript(self, filter_by=None):
        if filter_by is None:
            filter_by = dict()

        filtered_transcript = deepcopy(self.dialog_turn_messages)

        for key, value in filter_by.items():
            filtered_transcript = list(filter(lambda x: getattr(x, key) == value, filtered_transcript))

        return filtered_transcript
