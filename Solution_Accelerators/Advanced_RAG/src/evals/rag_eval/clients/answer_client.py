import argparse
import csv
import os
import time
import uuid

import pandas as pd
import requests
from tqdm import tqdm
from utils.logging_utils import log_response_info

from common.contracts.common.user_prompt import (
    PayloadType,
    UserPrompt,
    UserPromptPayload,
)
from common.contracts.session_manager.chat_request import ChatRequest


def get_answer(row: pd.Series, config: argparse.Namespace, requests_session: requests.Session) -> pd.DataFrame:
    """
    Get the answer from RAG Bot.
    """
    if config.conversation_id_prefix:
        conversation_id = f"{config.conversation_id_prefix}_{uuid.uuid4().hex[:6]}"
    else:
        conversation_id = f"{config.experiment_id}_{uuid.uuid4().hex[:6]}"

    chat_request = ChatRequest(
        conversation_id=conversation_id,
        user_id="anonymous",
        dialog_id=uuid.uuid4().hex,
        message=UserPrompt(payload=[UserPromptPayload(type=PayloadType.TEXT, value=row["question"])]),
    )
    # Overriding orchestrator or search configs if provided
    if config.orchestrator_config:
        chat_request.overrides.orchestrator_runtime.config_version = config.orchestrator_config

    if config.search_config:
        chat_request.overrides.search_overrides = config.search_config

    if config.search_topk:
        parsed_search_topk = int(config.search_topk)
        if chat_request.overrides.search_overrides is None:
            chat_request.overrides.search_overrides = {}
        chat_request.overrides.search_overrides.top = parsed_search_topk

    print(f"\nSending request: {chat_request.model_dump()}")
    response = requests_session.post(
        f"{config.address}/chat?scenario=rag",
        json=chat_request.model_dump(),
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        error = (
            f"Failed to get answer. CODE={response.status_code}, RESPONSE={response.text}, "
            f"QUESTION={row['question']}"
        )
        raise Exception(error)

    response_json = response.json()
    if response_json.get("error"):
        error = f"Failed to get answer. RESPONSE={response_json}, QUESTION={row['question']}"
        raise Exception(error)

    # Extract search queries and doc scores if needed
    search_queries = []
    doc_scores = []

    cognitive_search_skill_info = response_json["answer"]["steps_execution"]["cognitiveSearchSkill"]
    for query_info in cognitive_search_skill_info["step_input"]["search_queries"]:
        search_queries.append(query_info["search_query"])

    for search_results in cognitive_search_skill_info["step_output"]["results"]:
        result_scores = []
        for doc_info in search_results["search_results"]:
            try:
                score_col_name = "@search.reranker_score" if "@search.reranker_score" in doc_info else "search_score"
                result_scores.append(doc_info[score_col_name])
            except Exception as error:
                result_scores.append(0)
                if config.verbose:
                    print(f"Failed to get score for document: {doc_info}. Error: {error}")
        doc_scores.append(result_scores)

    if config.verbose:
        # Log the request/response
        request_body = {
            "conversation_id": conversation_id,
            "question": row["question"],
        }
        log_response_info(request_body, response_json, response, config)

    answer_frame_row = row.to_dict()
    answer_frame_row["search_queries"] = search_queries
    answer_frame_row["context_score"] = doc_scores
    answer_frame_row["contexts"] = response_json["answer"]["data_points"]
    answer_frame_row["answer"] = response_json["answer"]["answer_string"]
    answer_frame_row["cached_answer"] = False
    answer_frame = pd.DataFrame([answer_frame_row])
    return answer_frame


def get_benchmark_answers(config: argparse.Namespace, benchmark_questions: pd.DataFrame) -> pd.DataFrame:
    """
    Get the benchmark answers from RAG Bot.
    """
    requests_session = requests.Session()
    benchmark_answers_save_path = (
        f"{os.path.dirname(__file__)}/../results/{config.experiment_id}/benchmark_answers.csv"
    )
    answers_frame = None
    if os.path.exists(benchmark_answers_save_path):
        # If there's an existing partial run, load it
        answers_frame = pd.read_csv(benchmark_answers_save_path)
        print(f"Resuming from previous run. Loaded {len(answers_frame)} answers.")

    for index, row in tqdm(benchmark_questions.iterrows(), total=len(benchmark_questions), desc="Getting answers..."):
        # Save intermediate results
        if answers_frame is not None:
            answers_frame.to_csv(benchmark_answers_save_path, index=False, quoting=csv.QUOTE_ALL)

        is_answered_previosuly = (
            (answers_frame is not None)
            and (len(answers_frame) > index)
            and (answers_frame.iloc[index]["question"] == row["question"])
        )
        if is_answered_previosuly:
            continue

        awaiting_rag_bot_answer = True
        while awaiting_rag_bot_answer:
            try:
                current_answer_frame = get_answer(row, config, requests_session)
                if answers_frame is None:
                    answers_frame = current_answer_frame
                else:
                    answers_frame = pd.concat([answers_frame, current_answer_frame], ignore_index=True)
                awaiting_rag_bot_answer = False
            except Exception as error:
                print(f"Failed to get answer for question: {row['question']}. Error: {error}")
                print("Retrying in 30 seconds...")
                time.sleep(30)

    return answers_frame
