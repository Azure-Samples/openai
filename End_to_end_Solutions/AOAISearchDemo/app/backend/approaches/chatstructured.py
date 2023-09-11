import json
import pyodbc
import re
import pandas as pd
from backend.approaches.approach import Approach
from backend.cognition.openai_client import OpenAIClient
from backend.cognition.openai_settings import ChatCompletionsSettings
from backend.config import DefaultConfig
from backend.contracts.chat_response import Answer, ApproachType, ChatResponse
from backend.contracts.error import OutOfScopeException, UnauthorizedDBAccessException
from backend.utilities.openai_utils import generate_history_messages
from backend.utilities.prompt_composer_utils import trim_history, compute_tokens
from common.logging.log_helper import CustomLogger
from textwrap import dedent
from typing import Dict, List, Optional

# Structured information retrieval, using Azure SQL DB and Azure OpenAI APIs directly. It first uses OpenAI to generate
# a SQL query to retrieve data from a SQL database using dialog from the user. Then, after retrieving the data,
# it constructs a prompt injected with the retrieved table. Finally, it uses this prompt to request OpenAI to generate a
# completion (answer) that the user can understand.


class ChatStructuredApproach(Approach):
    def __init__(self, sql_connection_string: str, logger: CustomLogger):
        self.sql_connection_string = sql_connection_string
        self.logger = logger

    def run(self, history: List[Dict[str, str]], bot_config: dict, openai_client: OpenAIClient, overrides: Optional[dict] = None) -> any:        
        unauthorized_error_messages = ["I am not authorized to make changes to the data"]

        # STEP 1: Generate an SQL query using the chat history
        message_list = [{
            "role": "system",
            "content": dedent(bot_config["structured_query_nl_to_sql"]["system_prompt"])
                }
        ]
        
        if bot_config["structured_query_nl_to_sql"]["history"]["include"]:
            chat_history = generate_history_messages(
                history[:-1], bot_config["structured_query_nl_to_sql"]["history"])
            chat_history = trim_history(chat_history,
                                        bot_config["structured_query_nl_to_sql"]["model_params"]["total_max_tokens"] - compute_tokens(
                                            bot_config["structured_query_nl_to_sql"]["system_prompt"]) - bot_config["structured_query_nl_to_sql"]["openai_settings"]["max_tokens"],
                                        bot_config["structured_query_nl_to_sql"]["model_params"]["model_name"])
            message_list.extend(chat_history)

        message_list.append({"role": "user", "content": history[-1]['utterance'] + " SQL Code: "})

        nl_to_sql_response = openai_client.chat_completions(
            messages=message_list,
            openai_settings=ChatCompletionsSettings(**bot_config["structured_query_nl_to_sql"]["openai_settings"]),
            api_base=f"https://{DefaultConfig.AZURE_OPENAI_GPT4_SERVICE}.openai.azure.com",
            api_key=DefaultConfig.AZURE_OPENAI_GPT4_API_KEY
        )

        generated_sql_query = nl_to_sql_response['choices'][0]['message']['content']
        self.log_aoai_response_details(json.dumps(message_list), generated_sql_query, nl_to_sql_response)
        answer = Answer()

        # STEP 2: Run generated SQL query against the database
        sql_result = None

        if "ERROR:" in generated_sql_query:
            if any(message in generated_sql_query for message in unauthorized_error_messages):
                raise UnauthorizedDBAccessException("Error: I am not allowed to make changes to the data.")
            m = re.search(r"ERROR:(.*?)\.", generated_sql_query)
            if m:
                raise OutOfScopeException(message=m.group(1), suggested_classification=ApproachType.unstructured)

        answer.query = generated_sql_query
        try:
            with pyodbc.connect(self.sql_connection_string) as conn:
                df = pd.read_sql(generated_sql_query, conn)
                sql_result = str(df.to_string(index=False))
        except pd.errors.DatabaseError as e:
            raise OutOfScopeException(message=str(e), suggested_classification=ApproachType.unstructured)
        except Exception as e:
            raise Exception(f"Unknown error when querying SQL database: {str(e)}")

        # STEP 3: Format the SQL query and SQL result into a natural language response
        if sql_result is not None:
            answer.query_result = sql_result
            message_list = [{
                "role": "system",
                "content": dedent(bot_config["structured_final_answer_generation"]["system_prompt"])
            }]

            if bot_config["structured_final_answer_generation"]["history"]["include"]:
                message_list.extend(generate_history_messages(history[:-1], bot_config["structured_final_answer_generation"]["history"]))

            message_list.append({"role": "user", "content": "Question: " + history[-1]['utterance'] + "\nAnswer:\n" + sql_result})

            sql_result_to_nl_response = openai_client.chat_completions(
                messages=message_list,
                openai_settings=ChatCompletionsSettings(**bot_config["structured_final_answer_generation"]["openai_settings"]),
                api_base=f"https://{DefaultConfig.AZURE_OPENAI_GPT4_SERVICE}.openai.azure.com",
                api_key=DefaultConfig.AZURE_OPENAI_GPT4_API_KEY
            )

            formatted_sql_result = sql_result_to_nl_response['choices'][0]['message']['content']

            self.log_aoai_response_details(json.dumps(message_list), json.dumps(
                formatted_sql_result), sql_result_to_nl_response)

            answer.formatted_answer = formatted_sql_result

        return ChatResponse(classification=ApproachType.structured, answer=answer)

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
