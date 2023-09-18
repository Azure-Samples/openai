from textwrap import dedent
from typing import List

import openai
from backend.approaches.approach import Approach
from backend.cognition.openai_client import OpenAIClient
from backend.cognition.openai_settings import ChatCompletionsSettings
from backend.config import DefaultConfig
from backend.contracts.chat_response import ApproachType
from common.contracts.chat_session import DialogClassification
from common.logging.log_helper import CustomLogger


class ApproachClassifier(Approach):
    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def run(
        self, history: List[str], bot_config, openai_client: OpenAIClient
    ) -> ApproachType:

        message_list = [
            {
                "role": "system",
                "content": dedent(bot_config["approach_classifier"]["system_prompt"]),
            }
        ]

        if bot_config["approach_classifier"]["history"]["include"]:
            # TODO: SWE to add comment here explaining the logic
            for message in history[
                -((bot_config["approach_classifier"]["history"]["length"] * 2) + 1) :
            ]:
                if message["participant_type"] == "user":
                    message_list.append(
                        {"role": "user", "content": message["utterance"]}
                    )
                else:
                    classification = ""
                    if (
                        message["question_type"]
                        == DialogClassification.structured_query.name
                    ):
                        classification = ApproachType.structured.value
                    elif (
                        message["question_type"]
                        == DialogClassification.unstructured_query.name
                    ):
                        classification = ApproachType.unstructured.value
                    elif (
                        message["question_type"] == DialogClassification.chit_chat.name
                    ):
                        classification = ApproachType.chit_chat.value
                    else:
                        classification = ApproachType.unstructured.value
                    message_list.append(
                        {"role": "assistant", "content": classification}
                    )
        else:
            message_list.append({"role": "user", "content": history[-1]["utterance"]})
        try:
            response = openai_client.chat_completions(
                messages=message_list,
                openai_settings=ChatCompletionsSettings(
                    **bot_config["approach_classifier"]["openai_settings"]
                ),
                api_base=f"https://{DefaultConfig.AZURE_OPENAI_CLASSIFIER_SERVICE}.openai.azure.com",
                api_key=DefaultConfig.AZURE_OPENAI_CLASSIFIER_API_KEY,
            )
        except openai.error.InvalidRequestError as e:
            self.logger.error(f"OpenAI API Error: {e}", exc_info=True)
            raise e

        classification_response: str = response["choices"][0]["message"]["content"]
        self.log_aoai_response_details(
            f'Classification Prompt:{history[-1]["utterance"]}',
            f"Response: {classification_response}",
            response,
        )
        if classification_response == "1":
            return ApproachType.structured
        elif classification_response == "2":
            return ApproachType.unstructured
        elif classification_response == "3":
            return ApproachType.chit_chat
        elif classification_response == "4":
            # Continuation: Return last question type from history if it exists
            if len(history) > 1:
                last_question_type = history[-2]["question_type"]
                if last_question_type == DialogClassification.structured_query.value:
                    return ApproachType.structured
                elif (
                    last_question_type == DialogClassification.unstructured_query.value
                ):
                    return ApproachType.unstructured
                elif last_question_type == DialogClassification.chit_chat.value:
                    return ApproachType.chit_chat
                elif last_question_type == DialogClassification.inappropiate.value:
                    return ApproachType.inappropriate
                else:
                    raise Exception(f"Unknown question type: {last_question_type}")
            else:
                return ApproachType.unstructured
        elif classification_response == "5":
            # This is a special case where the user has typed something that violates guardrails because it contains illegal, harmful or malicious content
            return ApproachType.inappropriate
        else:
            return ApproachType.unstructured

    def log_aoai_response_details(self, prompt, result, aoai_response):
        addl_dimensions = {
            "completion_tokens": aoai_response.usage.get("completion_tokens", 0),
            "prompt_tokens": aoai_response.usage.prompt_tokens,
            "total_tokens": aoai_response.usage.total_tokens,
            "aoai_response[MS]": aoai_response.response_ms,
        }
        addl_properties = self.logger.get_updated_properties(addl_dimensions)
        self.logger.info(f"prompt: {prompt}, response: {result}", extra=addl_properties)
