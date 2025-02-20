import argparse
import json
import os

import requests


def log_response_info(
    request_body: dict,
    response_json: dict,
    response: requests.Response,
    params: argparse.Namespace
):
    """
    Log the request and response information.
    """
    http_info = {
        "request_body": request_body,
        "response": response_json,
        "status_code": response.status_code,
    }
    requests_logs_path = (
        f"{os.path.dirname(__file__)}/../results/{params.experiment_id}/requests_logs.json"
    )
    requests_logs = {"logs": []}
    if os.path.exists(requests_logs_path):
        requests_logs = json.load(open(requests_logs_path))

    requests_logs["logs"].append(http_info)
    json.dump(requests_logs, open(requests_logs_path, "w"), indent=4)
