# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import asyncio
from tqdm import tqdm
import pandas as pd
from typing import Union
import time

from azure.ai.projects.aio import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentThread,
    ChatCompletionAgent,
    ChatHistoryAgentThread,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai import (
    FunctionChoiceBehavior,
)

from azure.ai.agents.models import Agent as AIFoundryAgent
from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_factory_base import AgentFactory
from common.sk_service.service_configurator import get_service
from common.contracts.configuration.agent_config import (
    AzureAIAgentConfig,
    ChatCompletionAgentConfig,
    AIFoundryAgentConfig,
)
from common.agent_factory.agent_base import (
    AzureAIFoundryAgentBase,
    SemanticKernelAgentBase,
)
from common.contracts.configuration.orchestrator_config import (
    ResolvedOrchestratorConfig,
)

KERNEL_AZURE_CHAT_COMPLETION_SERVICE_ID = "default"


def create_kernel(config: ResolvedOrchestratorConfig) -> Kernel:
    kernel = Kernel()

    settings = AzureChatPromptExecutionSettings()
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    if config.service_configs:
        for service_config in config.service_configs:
            service_config = service_config.config_body
            print(f"Adding service to kernel: {service_config.service_id}")
            kernel.add_service(get_service(service_config))
    else:
        raise ValueError("No service configurations found.")
    return kernel


async def get_agent(agent_id: str, azure_ai_client: AIProjectClient, kernel: Kernel):
    agent_definition = await azure_ai_client.agents.get_agent(agent_id=agent_id)
    return AzureAIAgent(kernel=kernel, client=azure_ai_client, definition=agent_definition)


async def get_benchmark_answers(
    agent: Union[AzureAIAgent, ChatCompletionAgent, AIFoundryAgent],
    agent_config: Union[AzureAIAgentConfig, ChatCompletionAgentConfig, AIFoundryAgentConfig],
    benchmark_questions: pd.DataFrame,
    azure_ai_client: AIProjectClient,
    kernel: Kernel,
    run_dir_path: str,
):
    thread = None
    if isinstance(agent_config, AzureAIAgentConfig):
        thread = AzureAIAgentThread(client=azure_ai_client)
        await thread.create()
        print("Using AzureAIAgent, creating a new thread.")
        agent_instructions = agent_config.azure_ai_agent_config.instructions
    elif isinstance(agent_config, ChatCompletionAgentConfig):
        thread = ChatHistoryAgentThread()
        print("Using ChatCompletionAgent, creating a new thread.")
        agent_instructions = agent_config.prompt
    elif isinstance(agent_config, AIFoundryAgentConfig):
        thread = await azure_ai_client.agents.threads.create()
        print("Using AIFoundryAgent, creating a new thread.")
        agent_instructions = agent_config.instructions

    benchmark_answers_save_path = f"{run_dir_path}/benchmark_answers.csv"

    answer_frame = None
    for index, row in tqdm(
        benchmark_questions.iterrows(),
        total=len(benchmark_questions),
        desc="Getting answers...",
    ):

        current_answer_frame = await get_answers_from_agent(
            kernel=kernel,
            agent=agent,
            agent_instructions=agent_instructions,
            thread=thread,
            row=row,
            project_client=azure_ai_client,
        )

        if answer_frame is None:
            answer_frame = current_answer_frame
        else:
            answer_frame = pd.concat([answer_frame, current_answer_frame], ignore_index=True)

    answer_frame.to_csv(benchmark_answers_save_path)
    return benchmark_answers_save_path


async def get_answers_from_agent(
    kernel: Kernel,
    agent: Union[AzureAIAgent, ChatCompletionAgent, AIFoundryAgent],
    agent_instructions: str,
    thread: Union[AzureAIAgentThread, ChatHistoryAgentThread],
    row: pd.Series,
    project_client: AIProjectClient = None,
):
    answer_frame_row = row.to_dict()

    awaiting_answer = True
    timeout = 60  # seconds
    start_time = time.time()

    while awaiting_answer:
        if time.time() - start_time > timeout:
            print(
                f"Timeout while waiting for answer for question from agent: {row['query']}. Skipping to next question."
            )
            awaiting_answer = False
            continue
        try:
            if isinstance(agent, SemanticKernelAgentBase):
                response = await agent.invoke_with_runtime_config(
                    messages=row["query"],
                    thread=thread,
                    kernel=kernel,
                )
            elif isinstance(agent, AzureAIFoundryAgentBase):
                response = await agent.invoke_with_runtime_config(
                    messages=row["query"],
                    thread=thread,
                    project_client=project_client,
                )
            else:
                raise ValueError(
                    f"Unsupported agent type: {type(agent)}. Expected AzureAIAgent, ChatCompletionAgent, or AIFoundryAgent."
                )
            awaiting_answer = False
        except Exception as error:
            print(f"Failed to get answer for question: {row['query']}. Error: {error}")
            print("Retrying in 30 seconds...")
            await asyncio.sleep(30)

    if not response:
        print(f"No response received for question: {row['query']}. Skipping to next question.")
        return pd.DataFrame()

    if isinstance(response, str):
        answer_frame_row["response"] = response
    else:
        answer_frame_row["response"] = str(response.message.content)

    if agent_instructions:
        answer_frame_row["query"] = [
            {"role": "system", "content": agent_instructions},
            {"role": "user", "content": row["query"]},
        ]

    answer_frame = pd.DataFrame([answer_frame_row])
    return answer_frame
