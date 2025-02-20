import pytest
from unittest.mock import Mock
from common.contracts.data.prompt import History
from common.contracts.skills.search.api_models import SearchRagResult, SearchResponse, SearchResult
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import PrunedSearchResultsLog
from common.utilities import prompt_utils

def get_search_response() -> SearchResponse:
    sr_idx_result1 = SearchRagResult(
        id = "1",
        content = "Azure OpenAI Service provides REST API access to OpenAI's powerful language models including the GPT-4, GPT-4 Turbo with Vision, GPT-3.5-Turbo, and Embeddings model series. In addition, the new GPT-4 and GPT-3.5-Turbo model series have now reached general availability. These models can be easily adapted to your specific task including but not limited to content generation, summarization, image understanding, semantic search, and natural language to code translation. Users can access the service through REST APIs, Python SDK, or our web-based interface in the Azure OpenAI Studio.",
        section = "What is Azure OpenAI Service?",
        headings = ["Overview"],
        sourcePage = "Azure_OpenAI_Service_1.pdf",
        sourceFile = "Azure_OpenAI_Service.pdf",
        category = "Azure OpenAI Service"
    )
    ## token length of sr_idx_result1 {sourcePage}:{content}is 139 tokens

    sr_idx_result2 = SearchRagResult(
        id = "2",
        content = "At Microsoft, we're committed to the advancement of AI driven by principles that put people first. Generative models such as the ones available in Azure OpenAI have significant potential benefits, but without careful design and thoughtful mitigations, such models have the potential to generate incorrect or even harmful content. Microsoft has made significant investments to help guard against abuse and unintended harm, which includes requiring applicants to show well-defined use cases, incorporating Microsoft’s principles for responsible AI use, building content filters to support customers, and providing responsible AI implementation guidance to onboarded customers.",
        section = "What is Azure OpenAI Service?",
        headings = ["Responsible AI"],
        sourcePage = "Azure_OpenAI_Service_1.pdf",
        sourceFile = "Azure_OpenAI_Service.pdf",
        category = "Azure OpenAI Service"
    )
    ## token length of sr_idx_result2 {sourcePage}:{content}is 118 tokens

    sr_idx_result3 = SearchRagResult(
        id = "3",
        content = "Azure OpenAI Service gives customers advanced language AI with OpenAI GPT-4, GPT-3, Codex, DALL-E, Whisper, and text to speech models with the security and enterprise promise of Azure. Azure OpenAI co-develops the APIs with OpenAI, ensuring compatibility and a smooth transition from one to the other. With Azure OpenAI, customers get the security capabilities of Microsoft Azure while running the same models as OpenAI. Azure OpenAI offers private networking, regional availability, and responsible AI content filtering.",
        section = "What is Azure OpenAI Service?",
        headings = ["Comparing Azure OpenAI and OpenAI"],
        sourcePage = "Azure_OpenAI_Service_1.pdf",
        sourceFile = "Azure_OpenAI_Service.pdf",
        category = "Azure OpenAI Service"
    )
    ## token length of sr_idx_result3 {sourcePage}:{content}is 115 tokens

    search_result = SearchResult(
        search_query = "How does Azure OpenAI differs from OpenAI",
        search_id = "1",
        search_results=[sr_idx_result1, sr_idx_result2, sr_idx_result3],
        filter_succeeded = False
    )

    search_response =SearchResponse(
       results=[search_result],
    )
    return search_response

def get_messages():
    messages = [
        {
            "role": "user",
            "content": "What is Azure OpenAI"
        },
        {
            "role": "assistant",
            "content": "Azure OpenAI Service is a cloud-based offering from Microsoft that provides access to advanced language models developed by OpenAI, including the latest GPT-4, GPT-3.5-Turbo, and other AI models like Codex and DALL-E."
        },
        {
            "role": "user",
            "content": "How is that different from OpenAI"
        }
    ]
    return messages
    ## messages are around 63 tokens

def test_get_trimmed_search_results_trims_searchresponses_when_token_exceeds_limit():
    # Create an instance of the class containing the method to test
    mock_logger = Mock(spec=AppLogger)
    utils = prompt_utils.PromptHelper(mock_logger)

    max_token_length = 250
    model_name = "cl100k_base"
    history_settings = History(include=True, length=2, filter="")

    search_response = get_search_response()
    messages = get_messages()

    # Call the method to test
    result = utils.get_trimmed_search_results(search_response, max_token_length, model_name, messages, history_settings)

    # Assert that the result is as expected
    assert len(result.results[-1].search_results) == 1

    # log_details = PrunedSearchResultsLog(
    #     original_search_results_count=3,
    #     original_token_count=372,
    #     history_token_count=63,
    #     trimmed_search_results_count=1,
    #     final_token_count=139
    # )

    # mock_logger.info.assert_called_with(log_details.log_message, properties=log_details.model_dump())


def test_get_trimmed_search_results_returns_no_searchresults_when_noteven_single_search_result_fits_token_limit():
    # Create an instance of the class containing the method to test
    mock_logger = Mock(spec=AppLogger)
    utils = prompt_utils.PromptHelper(mock_logger)

    max_token_length = 100
    model_name = "cl100k_base"
    history_settings = History(include=True, length=3, filter="")

    search_response = get_search_response()
    messages = get_messages()

    # Call the method to test
    result = utils.get_trimmed_search_results(search_response, max_token_length, model_name, messages, history_settings)
    # print(result)

    # Assert that the result is as expected
    assert len(result.results[-1].search_results) == 0

    # log_details = PrunedSearchResultsLog(
    #     original_search_results_count=len(search_response.results[-1].search_results),
    #     original_token_count=372,
    #     history_token_count=63,
    #     trimmed_search_results_count=0,
    #     final_token_count=0
    # )

    # # mock_logger.info.assert_called_with(log_details.log_message, properties=log_details.model_dump())

def test_get_trimmed_search_results_ignores_history_tokens():
    # Create an instance of the class containing the method to test
    mock_logger = Mock(spec=AppLogger)
    utils = prompt_utils.PromptHelper(mock_logger)

    max_token_length = 150
    model_name = "cl100k_base"
    history_settings = History(include=False, length=0, filter="")

    search_response = get_search_response()
    messages = get_messages()

    # Call the method to test
    result = utils.get_trimmed_search_results(search_response, max_token_length, model_name, messages, history_settings)

    # Assert that the result is as expected
    assert len(result.results[-1].search_results) == 1

    log_details = PrunedSearchResultsLog(
        original_search_results_count=3,
        original_token_count=372,
        history_token_count=0,
        trimmed_search_results_count=1,
        final_token_count=139
    )

    # mock_logger.info.assert_called_with(log_details.log_message, properties=log_details.model_dump())