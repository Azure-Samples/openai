#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from flask import Flask, request, jsonify
from data.conversation_store import ConversationStore
from orchestrator import Orchestrator
from config import DefaultConfig

app = Flask(__name__)
orchestrator = Orchestrator()


@app.route("/query", methods=["POST"])
def run_flow():
    global orchestrator

    input_payload = dict(request.json)
    query = input_payload.get("query")
    conversation_id = input_payload.get("conversation_id")
    user_id = input_payload.get("user_id")

    conversation = orchestrator.get_or_create_conversation(conversation_id)
    agent_response = orchestrator.run_query(conversation, user_id, conversation_id, query)
    return agent_response


@app.route("/home", methods=["GET"])
def get_home():
    return "Welcome to AOAI VA Bot"


if __name__ == "__main__":
    app.run(port=DefaultConfig.PORT)
