import json
import os
import yaml

from typing import List
from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.openai.openai_chat_completions_configuration import OpenAIChatCompletionsConfiguration
from components.models.prompts_models import GPTFilteringPrompts


def load_prompts_file() -> GPTFilteringPrompts:
    try:

        file_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_filepath = os.path.join(file_dir, "prompts.yml")
        with open(prompts_filepath) as file:
            data = yaml.safe_load(file)
        if data is None:
            raise ValueError("The YAML file is empty.")
        return GPTFilteringPrompts(**data)

    except FileNotFoundError:
        raise FileNotFoundError(
            "Error: The specified YAML file does not exist.")
    except yaml.YAMLError as e:
        raise SyntaxError(f"Error while parsing YAML: {e}")
    except ValueError as e:
        raise ValueError(f"Error: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


prompts = load_prompts_file()


def _get_merged_descriptions(data: dict, description_keys: List[str] = []):
    if len(description_keys) == 0:
        descriptions = [value for key,
                        value in data.items() if "description" in key.lower()]
    else:
        descriptions = [value for key,
                        value in data.items() if key in description_keys]

    return ' '.join(descriptions)


def post_search_filter(openai_client: AzureOpenAIClient, original_search_query: str, search_results: List[dict], items_count: int = 1, id_key: str = "_id", description_keys: List[str] = []):
    system_prompt = prompts.postSearchFilterPrompts.systemPrompt.format(
        **{"items_count": items_count})

    # Assembling prompt input
    prompt_input = prompts.postSearchFilterPrompts.userPromptCollectionPrefix.format(
        **{"original_search_query": original_search_query})
    for result in search_results:
        # merging all descriptions
        merged_description = _get_merged_descriptions(result, description_keys)

        # extract product id
        product_ids = [value for key, value in result.items()
                      if id_key.lower() in key.lower()]
        if not product_ids:
            raise ValueError(f"Could not find 'id_key' in results")      
        
        product_id = product_ids[0]

        prompt_input += prompts.postSearchFilterPrompts.userPromptItemDescription.format(
            **{"product_id": product_id, "merged_description": merged_description})

    # Get response
    answer: str = openai_client.create_chat_completion(openai_configs=[
        OpenAIChatCompletionsConfiguration(
            system_prompt=system_prompt,
            user_prompt=prompt_input
        )])[0]

    # Process response
    try:
        filtered_items = json.loads(answer)

    except Exception as e:
        # invalid json format, attempting "," separation
        answer = answer.strip().lstrip("[").rstrip("]").replace('"',"")
        filtered_items = answer.split(",")

    # Filter results
    filtered_results = [item_data for item_data in search_results if item_data.get(
        id_key) in filtered_items]

    return filtered_results


def summarize_collection_items_description(openai_client: AzureOpenAIClient, category: str, search_results: List[dict], description_keys: List[str] = []):
    system_prompt = prompts.categorySummaryPrompts.systemPrompt

    # Assembling prompt input
    prompt_input = prompts.categorySummaryPrompts.userPromptCollectionPrefix.format(
        **{"category": category})
    for item in search_results:
        # merging all descriptions
        merged_description = _get_merged_descriptions(item, description_keys)

        prompt_input += prompts.categorySummaryPrompts.userPromptItemDescription.format(
            **{"merged_description": merged_description})

    # Get response
    return openai_client.create_chat_completion(openai_configs=[
        OpenAIChatCompletionsConfiguration(
            system_prompt=system_prompt,
            user_prompt=prompt_input
        )])[0]
