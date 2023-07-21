import json
from textwrap import dedent
from typing import List

import openai
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from backend.approaches.approach import Approach
from backend.contracts.chat_response import Answer, ApproachType, ChatResponse
from backend.contracts.error import OutOfScopeException
from backend.utilities.openai_utils import (generate_history_messages,
                                            generate_system_prompt)
from backend.utilities.prompt_composer_utils import \
    trim_history_and_index_combined
from backend.utilities.text import nonewlines
from common.logging.log_helper import CustomLogger


# Unstructured information retrieval, using the Cognitive Search and Azure OpenAI APIs directly. It first uses OpenAI to generate 
# a search query to retrieve top documents from a Cognitive Search index using dialog from the user. Then, after retrieving the 
# documents, it constructs a prompt injected with the retrieved documents. Finally, it uses this prompt to request OpenAI to generate a
# completion (answer) that the user can understand.
class ChatUnstructuredApproach(Approach):
    def __init__(self, search_client: SearchClient, sourcepage_field: str, content_field: str, logger: CustomLogger, search_threshold_percentage: float = 50):
        self.search_client = search_client
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.search_threshold_percentage = search_threshold_percentage
        self.logger = logger

    def run(self, history: List[dict], bot_config, overrides: dict) -> any:
        use_semantic_captions = True if overrides.get(
            "semantic_captions") else False
        top = overrides.get("top") or 20
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(
            exclude_category.replace("'", "''")) if exclude_category else None

        query_generation_messages = [
            {
                "role": "system",
                "content": dedent(bot_config["unstructured_search_query_generation"]["system_prompt"])
            }
        ]

        if bot_config["unstructured_search_query_generation"]["history"]["include"]:
            query_generation_messages.extend(generate_history_messages(history[:-1], bot_config["unstructured_search_query_generation"]["history"]))

        query_generation_messages.append({ "role": "user", "content": history[-1]["utterance"] + " Search Query: "})

        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question

        search_query_response = openai.ChatCompletion.create(
            messages=query_generation_messages,
            **bot_config["unstructured_search_query_generation"]["openai_settings"]
        )

        # Not sure why search results are coming with double quotes, so removing them. Double quotes making search to return no results
        search_query = search_query_response['choices'][0]['message']['content'].replace(
            '"', "")
        self.log_aoai_response_details(json.dumps(
            query_generation_messages), f'Generated Search Query: {search_query}', search_query_response)

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query
        if overrides.get("semantic_ranker"):
            r = self.search_client.search(search_query,
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC,
                                          query_language="en-us",
                                          semantic_configuration_name="default",
                                          query_answer= "extractive|count-3" if use_semantic_captions else None,
                                          query_caption="extractive" if use_semantic_captions else None,
                                          top=top
                                          )
            
        else:
            r = self.search_client.search(search_query, filter=filter, top=top)

        score_field = "@search.reranker_score" if overrides.get("semantic_ranker") else "@search.score"

        semantic_answers = r.get_answers() if use_semantic_captions else None

        parsed_results = list(r)

        max_score = max([parsed_result[score_field] for parsed_result in parsed_results])
        lower_bound = max_score * (self.search_threshold_percentage / 100)

        filtered_results = []
        
        if use_semantic_captions:
            if semantic_answers:
                for answers in semantic_answers:
                    # find the source page from the search results by matching key to id
                    doc = next((item for item in parsed_results if item["id"] == answers.key), None)
                    filtered_results.append(doc[self.sourcepage_field] + ": " + answers.text)
            else:
                for doc in parsed_results:
                    if doc[score_field] >= lower_bound:
                        filtered_results.append(doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])))
        else:
            for doc in parsed_results:
                if doc[score_field] >= lower_bound:
                    filtered_results.append(doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]))

        addl_dimensions = {"search_results_length": len(filtered_results)}
        properties = self.logger.get_updated_properties(addl_dimensions)
        self.logger.info(
            f"found {len(parsed_results)} results from search for query {search_query}. \
                After threshold filtering (Threshold: {self.search_threshold_percentage}) {len(filtered_results)} results from query are being used for answer generation", extra=properties)

        # STEP 3: Generate a contextual and content specific answer using the search results and chat history
        chat_history = list()
        if bot_config["unstructured_final_answer_generation"]["history"]["include"]:
            chat_history = generate_history_messages(history[:-1], bot_config["unstructured_final_answer_generation"]["history"])
        
        chat_history, search_content = trim_history_and_index_combined(chat_history, 
                                                                       filtered_results, 
                                                                       bot_config["unstructured_final_answer_generation"]["model_params"]["total_max_tokens"] - bot_config["unstructured_final_answer_generation"]["openai_settings"]["max_tokens"] - 300,
                                                                       bot_config["unstructured_final_answer_generation"]["model_params"]["model_name"])
        search_content = '\n'.join(search_content)
        contextual_answer_generation_messages = [
            {
                "role": "system",
                "content": generate_system_prompt(bot_config["unstructured_final_answer_generation"], {"context": search_content})
            }
        ]

        if bot_config["unstructured_final_answer_generation"]["history"]["include"]:
            contextual_answer_generation_messages.extend(chat_history)
        
        contextual_answer_generation_messages.append({ "role": "user", "content": history[-1]["utterance"]})

        contextual_answer_reponse = openai.ChatCompletion.create(
            messages=contextual_answer_generation_messages,
            **bot_config["unstructured_final_answer_generation"]["openai_settings"]
        )

        contextual_answer = contextual_answer_reponse['choices'][0]['message']['content']

        if contextual_answer.startswith("ERROR:"):
            contextual_answer = contextual_answer.replace("ERROR:", "").strip()
            raise OutOfScopeException(message=contextual_answer, suggested_classification=ApproachType.structured)

        self.log_aoai_response_details(json.dumps(
            contextual_answer_generation_messages), f'Search Result: {contextual_answer}', contextual_answer_reponse)

        formatted_query_generation_messages = self.format_messages(query_generation_messages)

        answer = Answer(formatted_answer=contextual_answer, query_generation_prompt=formatted_query_generation_messages, query=search_query)
        return ChatResponse(answer=answer, data_points=filtered_results, classification=ApproachType.unstructured)
    
    def format_messages(self, message) -> str:
        formatted_messages = ""
        for msg in message:
            formatted_messages += f"{msg['role']}: {msg['content']}\n"

        return formatted_messages

    def log_aoai_response_details(self, prompt, result, aoai_response):
        addl_dimensions = {
            "completion_tokens": aoai_response.usage.completion_tokens,
            "prompt_tokens": aoai_response.usage.prompt_tokens,
            "total_tokens": aoai_response.usage.total_tokens,
            "aoai_response[MS]": aoai_response.response_ms
        }
        addl_properties = self.logger.get_updated_properties(addl_dimensions)
        self.logger.info(
            f"prompt: {prompt}, response: {result}", extra=addl_properties)
