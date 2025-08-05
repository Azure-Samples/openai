# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import asyncio

from opentelemetry import trace

from config.default_config import DefaultConfig
from common.evals.eval_types.end_to_end_eval_base import EndToEndEvalBase
from common.contracts.configuration.eval_config import (
    EvaluationsConfig,
    EndToEndEvaluation,
)
from common.utilities.files import load_file

AGENT_CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

DefaultConfig.initialize()

tracer_provider = DefaultConfig.tracer_provider
tracer_provider.set_up()
tracer = trace.get_tracer(__name__)
logger = DefaultConfig.logger

default_runtime_config = load_file(
    os.path.join(
        os.path.dirname(__file__),
        "static",
        "eval_config.yaml",
    ),
    "yaml",
)


async def main():
    eval_jobs_config = EvaluationsConfig(**default_runtime_config)

    eval_name = input("Enter the evaluation name: ")

    if eval_name not in eval_jobs_config.evaluation_jobs:
        logger.error(f"Invalid evaluation name: {eval_name}")
        return

    current_eval_config = eval_jobs_config.evaluation_jobs[eval_name].config_body

    if isinstance(current_eval_config, EndToEndEvaluation):
        end_to_end_eval_job = EndToEndEvalBase(
            eval_config=current_eval_config,
            session_manager_uri=DefaultConfig.SESSION_MANAGER_URI,
            ai_project_endpoint=DefaultConfig.AZURE_AI_AGENT_ENDPOINT,
            azure_openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
            azure_openai_api_key=DefaultConfig.AZURE_OPENAI_KEY,
            azure_subscription_id=DefaultConfig.AZURE_SUBSCRIPTION_ID,
            azure_resource_group=DefaultConfig.AZURE_RESOURCE_GROUP,
            azure_workspace_name=DefaultConfig.AZURE_WORKSPACE_NAME,
            logger=logger,
        )
        await end_to_end_eval_job.evaluate()


asyncio.run(main())
