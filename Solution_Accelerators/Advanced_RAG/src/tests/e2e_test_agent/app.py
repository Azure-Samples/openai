import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime

import pytz
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from config import DefaultConfig
from core.conversation_client import ConversationClient
from core.utterance_builder import UtteranceBuilder
from flask import Flask, jsonify, request
from openai import AzureOpenAI
from utils.data_loader import load_data
from utils.files import load_file
from utils.prompt_utils import generate_system_prompt

DefaultConfig.initialize()
prompts_config = load_file(
    os.path.join(os.path.dirname(__file__), "prompts_config.yaml"), "yaml"
)

app = Flask(__name__)

def worker_function(conversation, date_string_prefix):
    try:
        client = ConversationClient(DefaultConfig.SESSION_MANAGER_URI + "/chat")
        azure_credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(azure_credential,
            "https://cognitiveservices.azure.com/.default")
        oai_client = AzureOpenAI(
            api_version="2024-02-15-preview",
            azure_endpoint=DefaultConfig.AZURE_OPENAI_GPT4_SERVICE,
            azure_ad_token_provider=token_provider
        )
        
        utterance_builder = UtteranceBuilder(oai_client, prompts_config, 3)
        conversation_depth = 0
        request_response_pairs = list()
        conversation_id = date_string_prefix + conversation[0]["conversation_id"]
        max_depth = max(DefaultConfig.CONVERSATION_DEPTH,len(conversation))

        while conversation_depth < max_depth:
            if conversation_depth < len(conversation):
                query = conversation[conversation_depth]["dialog"]
            else:
                query = utterance_builder.build_utterance(request_response_pairs)
            
            print(
                f"WORKER FUNCTION executing Query: {query} Conversation ID:{conversation_id}, Dialog ID: {conversation_depth}"
            )

            response = client.post_dialog(
                conversation_id=conversation_id, dialog_id=conversation_depth, dialog=query,
                overrides = {
                    "is_content_safety_enabled": False,
                    "search_overrides": {
                        "config_version": "demo-wto-tariff-profile-index_v2",
                        "top":30
                    }
                }
            )
            
            citation_accuracy = check_citation_accuracy(response, oai_client)

            request_response_pairs.append(
                deepcopy(
                    {
                        "conversation_id": conversation_id,
                        "dialog_id": conversation_depth,
                        "request": query,
                        "response": response,
                        "citation_accuracy": citation_accuracy,
                    }
                )
            )
            conversation_depth += 1

        return request_response_pairs
    except Exception as e:
        error_message = {
            "error": f"Error in worker_function: {e}",
            "conversation_id": conversation_id
        }
        print(f"Error in worker_function: {e}")
        return error_message


def check_citation_accuracy(session_manager_response, oai_client):
    citation_accuracy_summary = []
    if session_manager_response.get("error") is not None:
        return citation_accuracy_summary.append({'reasoning': session_manager_response.get("error"), 'citation_accurate': "False"})
    
    final_answer = session_manager_response.get("answer").get("answer_string")
    # remove formulas from final answer
    formula_pattern = r'\[[^\]]+\]'
    final_answer_text = re.sub(formula_pattern, "", final_answer)

    # get citations from final answer
    final_answer_citations = re.findall(r"\{\{([^}]+)\}\}", final_answer_text)

    data_points = session_manager_response.get("trimmed_merged_data_points")
    data_points_index = {}
    for data_point in data_points:
        file_name = data_point.split(":")[0]
        file_content = "||".join(data_point.split(":")[1:])
        data_points_index[file_name] = file_content

    for citation in final_answer_citations:
        citation_clean = citation.replace("{", "").replace("}", "")
        if citation_clean not in data_points_index:
            citation_accuracy = {'reasoning': f"Citation: {citation_clean} not found in reference documentation", 'citation_accurate': "False"}
            citation_accuracy_summary.append(citation_accuracy)
        else:
            reference_document = data_points_index[citation_clean]
            
            system_prompt = generate_system_prompt(prompts_config['check_citation'], {"final_answer_text": final_answer_text, "reference_document": reference_document})

            completion_response = oai_client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}],
                **prompts_config["check_citation"]["openai_settings"]
            )

            if completion_response.choices[0].finish_reason == "stop":
                response = json.loads(completion_response.choices[0].message.content)
                citation_accuracy_summary.append(response)

    return citation_accuracy_summary

def load_and_execute():
    print("STARTING LOAD AND EXECUTE")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    data = load_data(os.path.join(current_dir, "data", "queries.yaml"))

    date_string_prefix = datetime.now().strftime("%d_%b_%H%M%S_")

    def callback_wrapper(conversation):
        return worker_function(conversation, date_string_prefix)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(callback_wrapper, data.values()))

    output_filename = date_string_prefix + "results.yaml"
    with open(output_filename, "w") as f:
        yaml.dump(results, f, default_flow_style=False)

    blob_service_client = BlobServiceClient(account_url=f"https://{DefaultConfig.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net", 
                                            credential=DefaultAzureCredential())
    blob_client = blob_service_client.get_blob_client(container=DefaultConfig.AZURE_BLOB_CONTAINER_NAME_E2E_TEST, 
                                                      blob=output_filename)
    results_yaml = yaml.dump(results, default_flow_style=False)
    blob_client.upload_blob(results_yaml, overwrite=True)

    return results


@app.route("/e2etest", methods=["GET"])
def healthz():
    return "TEST AGENT IS HEALTHY"


@app.route("/e2etest/run", methods=["GET"])
def run_test_agent():
    load_and_execute()
    return "Executed the test agent manually."

@app.route("/e2etest/jobs", methods=["GET"])
def get_scheduled_jobs():
    jobs = scheduler.get_jobs()
    job_list = [{"id": job.id, "next_run_time": str(job.next_run_time)} for job in jobs]
    return jsonify(job_list), 200

@app.route("/e2etest/jobs/clear", methods=["POST"])
def clear_jobs():
    if scheduler:
        scheduler.remove_all_jobs()
        return "Cleared all jobs."
    return "No scheduler defined."

@app.route("/e2etest/jobs/schedule", methods=["POST"])
def schedule_job():
    data = request.get_json()
    try:
        hour = data.get("hour", 22)
        minute = data.get("minute", 0)
        second = data.get("second", 0)
        timezone_str = data.get("timezone", "America/Los_Angeles")
        timezone = pytz.timezone(timezone_str)

        scheduler.add_job(
            load_and_execute,
            "cron",
            hour=hour,
            minute=minute,
            second=second,
            timezone=timezone,
        )
        return jsonify({"message": "Job scheduled successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/e2etest/jobs/stop", methods=["POST"])
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        return "Scheduler stopped."
    else:
        return "Scheduler is not running."
    
# Scheduler setup - runs the test agent at 10:00 PM PST / 7:00 AM CET
scheduler = BackgroundScheduler()
scheduler.add_job(
    load_and_execute,
    "cron",
    hour=22,
    minute=0,
    second=0,
    timezone=pytz.timezone("America/Los_Angeles"),
)
scheduler.start()

if __name__ == "__main__":
    app.run(port=5051)
