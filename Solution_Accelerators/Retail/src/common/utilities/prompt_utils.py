from ast import Dict
import json
import tiktoken
from common.contracts.data.prompt import History, Prompt
from typing import List, Optional
from common.contracts.skills.search.api_models import SearchResponse, SearchRagResult, SearchRetailResult
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import PrunedSearchResultsLog

class PromptHelper():
    def __init__(self, logger: AppLogger) -> None:
        self.logger = logger

    def compute_tokens(input_str: str, model_name: Optional[str] = "gpt-4") -> int:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(input_str))

    def generate_history_messages(self, history, config):
        formatted_messages = []

        user_message_format = config["user_message_format"]
        assistant_message_format = config["assistant_message_format"]
        history_length = config["length"]

        for message in history[-(history_length*2):]:
            # load the message components from history
            message_values = message
            role = ""

            # This is dont since assistant messages can have multiple components like "sql_query", "sql_results" etc.
            # TODO: unify all messages to support multiple components natively
            if message["role"] == "user":
                formatted_message = user_message_format
                role = "user"
            else:
                formatted_message = assistant_message_format
                message_values = json.loads(message["content"])
                role = "assistant"

            for key in message_values:
                if message_values[key] is not None:
                    formatted_message = formatted_message.replace("{" + key + "}", message_values[key])

            formatted_messages.append({"role": role, "content": formatted_message})

        return formatted_messages

    def generate_system_message(self, llm_prompt:Prompt, trimmed_search_results: List[SearchRagResult]):
        aoai_context_str = ""
        for search_result in trimmed_search_results:
            aoai_context_str += ('\n' + search_result.to_string())

        prompt_arguments = {"context": aoai_context_str}
        system_prompt = llm_prompt.system_prompt.update_template_with_args(prompt_arguments)
        return system_prompt

    def generate_user_message(self, llm_prompt:Prompt, trimmed_search_results: List[SearchRagResult], user_query:str):
        aoai_context_str = ""
        for search_result in trimmed_search_results:
            aoai_context_str += ('\n' + search_result.to_string())

        prompt_arguments = {"context": aoai_context_str, "user_query": user_query}
        if llm_prompt.user_prompt:
            user_prompt = llm_prompt.user_prompt.update_template_with_args(prompt_arguments)
        else:
            user_prompt = user_query
        return user_prompt
    
    def generate_retail_user_message(self, llm_prompt:Prompt, reprhased_query: str, retail_search_results: List[SearchRetailResult]):
        aoai_context_str = ""
        for search_result in retail_search_results:
            aoai_context_str += ('\n' + search_result.to_json_for_prompt())

        prompt_arguments = {"rephrased_query": reprhased_query, "list_of_products": aoai_context_str}
        if llm_prompt.user_prompt:
            user_prompt = llm_prompt.user_prompt.update_template_with_args(prompt_arguments)
        else:
            user_prompt = reprhased_query
        return user_prompt
    
    def generate_retail_system_message(self, llm_prompt:Prompt, reprhased_query: str, retail_search_results: List[SearchRetailResult]):
        aoai_context_str = ""
        for search_result in retail_search_results:
            aoai_context_str += ('\n' + search_result.to_json_for_prompt())

        prompt_arguments = {"rephrased_query": reprhased_query, "list_of_products": aoai_context_str}
        system_prompt = llm_prompt.system_prompt.update_template_with_args(prompt_arguments)
        return system_prompt

    def get_user_message_with_history(self, messages, llm_prompt:Prompt):
        user_prompt = llm_prompt.user_prompt
        history_len = user_prompt.history.length
        # user_prompt_template = user_prompt.template

        user_request_and_response_list = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role == "user":
                user_request_and_response_list.append(f"User: {content}")
            elif role == "assistant":
                user_request_and_response_list.append(f"Bot: {content}")

        if history_len:
            pruned_user_request_and_response_list = user_request_and_response_list[-((history_len * 2) + 1):]
        else:
            pruned_user_request_and_response_list = user_request_and_response_list

        # remove last message as that is the current user message
        pruned_user_request_and_response_list.pop() if pruned_user_request_and_response_list else ""
        last_user_message = messages[-1]["content"] if messages else ""

        # convert list to string
        user_request_and_response_str = '\n'.join(pruned_user_request_and_response_list)
        arguments = {
            "user_request_and_response_str":user_request_and_response_str,
            "last_user_message":last_user_message
        }
        format_str = user_prompt.update_template_with_args(arguments)
        return format_str

    def get_trimmed_search_results(self, search_results: List[SearchRagResult],
                                   max_token_length: int,
                                   model_name,
                                   messages: List[Dict],
                                   history_settings: History,
                               ) -> List[SearchRagResult]:
        encoding = tiktoken.get_encoding(model_name) # need to use encoding_for_model for gpt based models

        # reduce max token based on history
        pruned_history = self.get_history_messages(messages, history_settings.length)
        history_len = history_settings.length

        history_str = ""
        if len(pruned_history) > 0 and history_len > 0:
            for message in pruned_history:
                history_str += f"{message['role']}: {message['content']}\n"

        history_token_length = len(encoding.encode(history_str))
        max_token_length = max_token_length - history_token_length

        # reduce search context based on available max token length

        context_str = ""
        original_search_results_count = len(search_results)

        for search_result in search_results:
            context_str += ('\n' + search_result.to_string())

        context_token_length = len(encoding.encode(context_str))
        current_token_length = context_token_length

        while current_token_length > max_token_length:
            context_str = ""
            # This will work as we only have one SearchResult in the list but needs to reviewed if we have more than one SearchResult
            search_results.pop()
            for search_result in search_results:
                context_str += ('\n' + search_result.to_string())
            current_token_length = len(encoding.encode(context_str))

        log_details = PrunedSearchResultsLog(
            original_search_results_count=original_search_results_count,
            original_token_count=context_token_length,
            history_token_count=history_token_length,
            trimmed_search_results_count=len(search_results),
            final_token_count=current_token_length
        )

        self.logger.info(log_details.log_message, properties=log_details.model_dump())
        return search_results

    def get_history_messages(self, messages: List[Dict], last_n: int):
        pruned_history = []
        if last_n:
            pruned_history = messages[-((last_n * 2) + 1):]
        else:
            pruned_history = messages

        # remove last message as that is the current user message
        pruned_history.pop() if pruned_history else ""

        return pruned_history