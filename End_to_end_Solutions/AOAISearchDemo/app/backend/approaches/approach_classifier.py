from textwrap import dedent
from typing import List

import openai
from backend.approaches.approach import Approach
from backend.contracts.chat_response import ApproachType
from common.contracts.chat_session import DialogClassification
from common.logging.log_helper import CustomLogger


class ApproachClassifier(Approach):
    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def run(self, history: List[str], bot_config) -> ApproachType:

        message_list = [
            {
                "role": "system",
                "content": dedent(bot_config["approach_classifier"]["system_prompt"])
            }
        ]

        if bot_config["approach_classifier"]["history"]["include"]:
            for message in history[-((bot_config["approach_classifier"]["history"]["length"]*2) + 1):]:
                if message["participant_type"] == "user":
                    message_list.append(
                        {"role": "user", "content": message["utterance"]})
                else:
                    classification = ''
                    if message['question_type'] == DialogClassification.structured_query.name:
                        classification = ApproachType.structured.value
                    elif message['question_type'] == DialogClassification.unstructured_query.name:
                        classification = ApproachType.unstructured.value
                    elif message['question_type'] == DialogClassification.chit_chat.name:
                        classification = ApproachType.chit_chat.value
                    else:
                        classification = ApproachType.unstructured.value
                    message_list.append(
                        {"role": "assistant", "content": classification})
        else:
            message_list.append(
                {"role": "user", "content": history[-1]["utterance"]})
        try:
            response = openai.ChatCompletion.create(
                messages=message_list,
                **bot_config["approach_classifier"]["openai_settings"]
            )
        except openai.error.InvalidRequestError as e:
            self.logger.error(
                f"OpenAI API Error: {e.message}", exc_info=True)
            raise e

        q: str = response['choices'][0]['message']['content']
        self.log_aoai_response_details(
            f'Classification Prompt:{history[-1]["utterance"]}', f'Response: {q}', response)

        if q == "1":
            return ApproachType.structured
        elif q == "2":
            return ApproachType.unstructured
        elif q == "3":
            return ApproachType.chit_chat
        elif q == "4":
            # Continuation: Return last question type from history if it exists
            if len(history) > 1:
                last_question_type = history[-2]['question_type']
                if last_question_type == DialogClassification.structured_query.value:
                    return ApproachType.structured
                elif last_question_type == DialogClassification.unstructured_query.value:
                    return ApproachType.unstructured
                elif last_question_type == DialogClassification.chit_chat.value:
                    return ApproachType.chit_chat
                else:
                    raise Exception(
                        f"Unknown question type: {last_question_type}")
            else:
                return ApproachType.unstructured
        else:
            return ApproachType.unstructured

    def log_aoai_response_details(self, prompt, result, aoai_response):
        addl_dimensions = {
            "completion_tokens": aoai_response.usage.get("completion_tokens", 0),
            "prompt_tokens": aoai_response.usage.prompt_tokens,
            "total_tokens": aoai_response.usage.total_tokens,
            "aoai_response[MS]": aoai_response.response_ms
        }
        addl_properties = self.logger.get_updated_properties(addl_dimensions)
        self.logger.info(
            f"prompt: {prompt}, response: {result}", extra=addl_properties)
