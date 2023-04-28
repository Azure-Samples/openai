#
# Todo: can mostly be removed post integration with cosmos.
#
class DialogTurn:
    def __init__(self, **kwargs):
        self.user_utterance = kwargs.get("user_utterance", "")
        self.agent_response = kwargs.get("agent_response", "")
        self.topic_classifier_response = kwargs.get("topic_classifier_response", "")
