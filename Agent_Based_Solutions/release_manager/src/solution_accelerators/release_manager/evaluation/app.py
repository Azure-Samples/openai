# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import asyncio

from opentelemetry import trace

from config.default_config import DefaultConfig
from common.evals.eval_types.end_to_end_eval_base import EndToEndEvalBase
from common.contracts.configuration.eval_config import (
    EvaluationsConfig,
    AgentEvaluation,
    EndToEndEvaluation,
)
from common.utilities.files import load_file

from release_manager_agent_evaluation import ReleaseManagerAgentEval
from solution_accelerators.release_manager.models.jira_settings import JiraSettings
from solution_accelerators.release_manager.models.devops_settings import DevOpsSettings

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

    if isinstance(current_eval_config, AgentEvaluation):
        agent_eval_job = ReleaseManagerAgentEval(
            eval_config=current_eval_config,
            ai_project_conn_str=DefaultConfig.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING,
            azure_openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
            azure_subscription_id=DefaultConfig.AZURE_SUBSCRIPTION_ID,
            azure_resource_group=DefaultConfig.AZURE_RESOURCE_GROUP,
            azure_workspace_name=DefaultConfig.AZURE_WORKSPACE_NAME,
            jira_settings=JiraSettings(
                server_url=DefaultConfig.JIRA_SERVER_ENDPOINT,
                username=DefaultConfig.JIRA_SERVER_USERNAME,
                password=DefaultConfig.JIRA_SERVER_PASSWORD,
                config_file_path=AGENT_CONFIG_FILE_PATH
            ),
            devops_settings=DevOpsSettings(
                server_url=DefaultConfig.DEVOPS_DATABASE_SERVER_ENDPOINT,
                username=DefaultConfig.DEVOPS_DATABASE_SERVER_USERNAME,
                password=DefaultConfig.DEVOPS_DATABASE_SERVER_PASSWORD,
                database_name=DefaultConfig.DEVOPS_DATABASE_NAME,
                database_table_name=DefaultConfig.DEVOPS_DATABASE_TABLE_NAME,
                config_file_path=AGENT_CONFIG_FILE_PATH
            ),
            logger=logger,
        )
        await agent_eval_job.evaluate()

    elif isinstance(current_eval_config, EndToEndEvaluation):
        end_to_end_eval_job = EndToEndEvalBase(
            eval_config=current_eval_config,
            session_manager_uri=DefaultConfig.SESSION_MANAGER_URI,
            ai_project_conn_str=DefaultConfig.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING,
            azure_openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
            azure_subscription_id=DefaultConfig.AZURE_SUBSCRIPTION_ID,
            azure_resource_group=DefaultConfig.AZURE_RESOURCE_GROUP,
            azure_workspace_name=DefaultConfig.AZURE_WORKSPACE_NAME,
            logger=logger,
        )
        await end_to_end_eval_job.evaluate()

asyncio.run(main())
