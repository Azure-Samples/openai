# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import websockets
import uuid
import time
import json
import pandas as pd
from tqdm import tqdm


from common.contracts.common.user_query import (
    PayloadType,
    UserQuery,
    UserQueryPayload,
)
from common.contracts.session_manager.request import Request

async def get_answer_from_session_manager(session_manager_uri: str, current_row: pd.Series) -> pd.DataFrame:
    print(f"Getting answer for question: {current_row['query']}")
    session_id = uuid.uuid4()

    ws_uri = f"ws://{session_manager_uri}/api/query?session_id={session_id}"
    print(f"Connecting to session manager at {ws_uri}")
    async with websockets.connect(ws_uri, ping_interval=None) as websocket:
        request = Request(
            dialog_id="dialog1",
            user_id="anonymous",
            message=UserQuery(
                payload=[
                    UserQueryPayload(
                        type=PayloadType.TEXT,
                        value=current_row['query']
                    )
                ]
            ),
        )
        await websocket.send(request.model_dump_json())

        timeout = 180  # seconds
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout while waiting for final answer from the session manager for question: {current_row['query']}")
            try:
                response = await websocket.recv()
                response = json.loads(response)
                if response.get("answer").get("is_final") == True:
                    answer_frame_row = current_row.to_dict()
                    answer_frame_row["response"] = str(response.get("answer").get("answer_string"))
                    answer_frame = pd.DataFrame([answer_frame_row])
                    return answer_frame
            except websockets.exceptions.ConnectionClosedOK as ex:
                error = f"Failed to get answer. Connection closed by the server: {ex}, QUESTION={current_row['query']}"
                raise Exception(error)
            except websockets.exceptions.ConnectionClosedError as ex:
                error = f"Failed to get answer. Connection closed by the server: {ex}, QUESTION={current_row['query']}"
                raise Exception(error)

async def get_benchmark_answers(benchmark_questions: pd.DataFrame, session_manager_uri: str, run_dir_path: str) -> str:
    """
    Get the benchmark answers from Session Manager.
    """
    benchmark_answers_save_path = f"{run_dir_path}/benchmark_answers.csv"

    answers_frame = None

    for index, row in tqdm(benchmark_questions.iterrows(), total=len(benchmark_questions), desc="Getting answers..."):

        awaiting_answer = True
        timeout = 180  # seconds
        start_time = time.time()
        while awaiting_answer:
            if time.time() - start_time > timeout:
                print(f"Timeout while waiting for answer from session manager for question: {row['query']}. Skipping to next question.")
                awaiting_answer = False
                continue
            try:
                current_answer_frame = await get_answer_from_session_manager(session_manager_uri=session_manager_uri, current_row=row)
                if answers_frame is None:
                    answers_frame = current_answer_frame
                else:
                    answers_frame = pd.concat([answers_frame, current_answer_frame], ignore_index=True)
                awaiting_answer = False
            except Exception as error:
                print(f"Failed to get answer for question: {row['query']}. Error: {error}")
                print("Retrying in 30 seconds...")
                time.sleep(30)
    print(f"Saving answers to {benchmark_answers_save_path}")
    answers_frame.to_csv(benchmark_answers_save_path)
    return benchmark_answers_save_path