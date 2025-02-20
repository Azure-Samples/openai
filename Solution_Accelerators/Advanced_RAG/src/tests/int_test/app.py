import os
import re

import pytest
import requests
import yaml
from config import DefaultConfig
from model.data_model import ResultAssertion, TestCase, TestDialog
from utils.websocket_handler import WebSocketHandler

from common.contracts.common.user_prompt import UserPrompt, UserPromptPayload
from common.contracts.session_manager.chat_request import ChatRequest
from common.contracts.session_manager.chat_response import ChatResponse

DefaultConfig.initialize()
logger = DefaultConfig.logger


def load_test_cases(file_path: str = None) -> list:
    # setup test cases
    file_path = f"{os.path.dirname(__file__)}/{file_path}"
    with open(file_path, "r") as f:
        test_cases_yaml = yaml.safe_load(f)

    # load test_cases into Pydantic model
    test_cases = []
    for test_case in test_cases_yaml["test_cases"]:
        # add a 6 char random string to conversation_id to make them unique
        uid = os.urandom(3).hex()
        test_case["conversation"]["conversation_id"] = f"{test_case['conversation']['conversation_id']}_{uid}"
        test_case = TestCase(**test_case)
        test_cases.append(test_case)

    return test_cases


rag_test_cases = []
retail_test_cases = []

if DefaultConfig.TEST_CASE_SCENARIO.lower() in ["rag", "all"]:
    rag_test_cases = load_test_cases("test_cases_rag.yaml")
if DefaultConfig.TEST_CASE_SCENARIO.lower() in ["retail", "all"]:
    retail_test_cases = load_test_cases("test_cases_retail.yaml")

test_cases = rag_test_cases + retail_test_cases
test_case_ids = [test_case.test_case for test_case in test_cases]


@pytest.mark.parametrize("test_case", test_cases, ids=test_case_ids)
@pytest.mark.asyncio
async def test_run_integration_test(test_case: TestCase):
    logger.info("Starting integration test")

    # Testing HTTP API
    if test_case.communication_protocol in ["http", "all"]:
        run_test_case_over_http(test_case)

    # if the test case also needs to be tested on websocket API then run the test case on websocket API
    if test_case.communication_protocol in ["websocket", "all"]:
        await run_test_case_over_websocket(test_case)


def run_test_case_over_http(test_case: TestCase):
    for dialog in test_case.conversation.dialogs:
        user_prompt = ""
        for payload in dialog.message.payload:
            if payload.type == "text":
                user_prompt = user_prompt + payload.value + "\n"
        msg = f"Running test case over HTTP: '{test_case.test_case}' for dialog_ID: {dialog.dialog_id}  with dialog: {user_prompt}"
        logger.info(msg)
        chat_request = get_chat_request(test_case, dialog)
        logger.info(f"Payload: {chat_request.model_dump()}")

        # run test cases
        query_params = {"scenario": test_case.scenario}
        response = send_request(payload=chat_request, query_params=query_params)

        assert_response(dialog, ChatResponse(**response.json()))


async def run_test_case_over_websocket(test_case):
    ws = WebSocketHandler(DefaultConfig.SESSION_MANAGER_URL, logger, connection_id="", scenario=test_case.scenario)

    for dialog in test_case.conversation.dialogs:
        user_prompt = ""
        for payload in dialog.message.payload:
            if payload.type == "text":
                user_prompt = user_prompt + payload.value + "\n"
        msg = f"Running test case over Websocket: '{test_case.test_case}' for dialog_ID: {dialog.dialog_id}  with dialog: {user_prompt}"
        logger.info(msg)
        chat_request = get_chat_request(test_case, dialog)
        logger.info(f"Payload: {chat_request.model_dump()}")

        # run test cases
        response = await ws.send_and_receive(chat_request.model_dump(), max_retries=3, retry_delay=5)
        assert_response(dialog, ChatResponse(**response))
    await ws.close()


def assert_response(dialog: TestDialog, chat_response: ChatResponse):
    response_assertion = dialog.assertion.response_assertion
    if response_assertion:
        # assert eval(f"response.{response_assertion}")
        assert chat_response.error is None

        logger.info(f"Passed check for response status code: {response_assertion}.")

    check_presence_citation = dialog.assertion.check_presence_citation
    if check_presence_citation:
        check_citation_presence(chat_response)
    result_assertion = dialog.assertion.result_assertion
    if result_assertion:
        validate_result(chat_response, result_assertion)


# @retry(tries=5, delay=60, backoff=1.1, logger=logger)
def send_request(payload: ChatRequest, query_params: dict = None):
    return requests.post(DefaultConfig.SESSION_MANAGER_URL + "/chat", json=payload.model_dump(), params=query_params)


def is_search_string_array_in_result(search_str_array: list, search_result: dict) -> bool:
    for search_str in search_str_array:
        if (
            search_str.lower() in search_result.get("detailDescription", "").lower()
            or search_str.lower() in search_result.get("productName", "").lower()
        ):
            return True
    return False


def validate_result(chat_response: ChatResponse, result_assertion: ResultAssertion):
    flattened_search_results = []
    search_results = []
    if chat_response.answer.steps_execution:
        steps = chat_response.answer.steps_execution
        search_results = steps.get("cognitiveSearchSkill", {}).get("step_output", {}).get("results", [])
    for search_result in search_results:
        flattened_search_results.extend(search_result.get("search_results", []))

    if result_assertion.result_count:
        eval_str = result_assertion.result_count.replace("result_count", "flattened_search_results")
        assert eval(eval_str)
        logger.info(f"Passed count of search results: {eval_str}.")

    if result_assertion.product_description_includes_keywords:
        # ensure all the strings are included in at least one of the search results
        found = False
        for result in flattened_search_results:
            if is_search_string_array_in_result(result_assertion.product_description_includes_keywords, result):
                found = True
                break

        assert found
        logger.info(
            f"Passed keywords check - product_description_includes_keywords: {result_assertion.product_description_includes_keywords}."
        )


def check_citation_presence(chat_response: ChatResponse):
    # session_manager_response = response
    # final_answer = session_manager_response.get("answer").get("answer_string")
    final_answer = chat_response.answer.answer_string
    final_answer_citations = re.findall(r"\{\{([^}]+)\}\}", final_answer)

    # data_points = session_manager_response.get("answer").get("data_points")
    data_points = chat_response.answer.data_points
    data_points_index = {}
    for data_point in data_points:
        file_name = data_point.split(":")[0]
        file_content = "||".join(data_point.split(":")[1:])
        data_points_index[file_name] = file_content

    for citation in final_answer_citations:
        citation_clean = citation.replace("{", "").replace("}", "")
        assert citation_clean in data_points_index


def get_chat_request(test_case: TestCase, dialog: TestDialog) -> ChatRequest:
    chat_request = ChatRequest(
        conversation_id=test_case.conversation.conversation_id,
        user_id=test_case.conversation.user_id,
        dialog_id=dialog.dialog_id,
        message=dialog.message,
        overrides=dialog.overrides,
        response_mode="json",
        user_profile=test_case.conversation.user_profile,
    )
    return chat_request
