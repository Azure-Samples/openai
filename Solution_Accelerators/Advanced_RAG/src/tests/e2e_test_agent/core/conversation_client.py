import requests
from retry import retry
from common.contracts.session_manager.chat_request import ChatRequest
from common.contracts.common.user_prompt import UserPrompt, UserPromptPayload, PayloadType

class ConversationClient:
    def __init__(self, endpoint_url, max_retries=3, retry_delay=20):
        self.endpoint_url = endpoint_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @retry(delay=60, backoff=1.1, tries=5)
    def post_dialog(self, dialog, conversation_id, dialog_id, user_id, overrides={}):
        chat_request = ChatRequest(
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            dialog_id=str(dialog_id),
            message=UserPrompt(
                UserPromptPayload(
                    type=PayloadType.TEXT,
                    value=dialog
                )
            ),
            overrides=overrides
        )

        headers = { "Content-Type": "application/json" }
        response = requests.post(self.endpoint_url, json=chat_request.model_dump_json(), headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Request failed with status code {response.status_code} and message {response.text}"}