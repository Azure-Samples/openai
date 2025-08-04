# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Union

from azure.ai.projects.models import EvaluatorConfiguration, EvaluatorIds
from azure.ai.evaluation import (
    IntentResolutionEvaluator,
    TaskAdherenceEvaluator,
    AzureOpenAIModelConfiguration,
    OpenAIModelConfiguration,
)

from common.contracts.configuration.eval_config import (
    BuiltinMetricsConfig,
    AgentEvalMetricsConfig,
    AzureOpenAIServiceSettings,
    OpenAIServiceSettings,
)

"""
In order to use built in evaluators which are available in Foundry evaluators library, we need to provide their ids.
Foundry will use these ids to fetch the evaluators from the library. As of now, these ids are hardcoded but in future SDK will be updated to 
handle this in a more dynamic way.
"""
evaluator_id = {
    "GROUNDENESS": EvaluatorIds.GROUNDEDNESS.value,
    "RELEVANCE": EvaluatorIds.RELEVANCE.value,
    "SIMILARITY": EvaluatorIds.SIMILARITY.value,
    "F1_SCORE": EvaluatorIds.F1_SCORE.value,
    "COHERENCE": EvaluatorIds.COHERENCE.value,
    "INTENT_RESOLUTION": EvaluatorIds.INTENT_RESOLUTION.value,
    "TASK_ADHERENCE": EvaluatorIds.TASK_ADHERENCE.value,
}

"""
Following evaluators are specific agent evaluators. As of now these evaluators are not available in Foundry evaluators library.
So there is no id available for them and can not be used with cloud evaluation. We have added specific function to prepare these agents for local 
evaluation.
"""
agent_evaluators = {
    "INTENT_RESOLUTION": IntentResolutionEvaluator,
    "TASK_ADHERENCE": TaskAdherenceEvaluator,
}


def get_evaluators(
    evaluators_config: dict[str, Union[BuiltinMetricsConfig, AgentEvalMetricsConfig]],
):
    """
    Prepares evaluators based on the provided configuration for cloud evaluation. For cloud evaluation, evaluators should be in format defined below:
    {
        "metric_name": EvaluatorConfiguration(
            id="evaluator_id",
            init_params={
                "deployment_name": model_config_based_on_provided_config
            }
        )
    }
    """
    evaluators = {}
    for metric in evaluators_config:
        metric_config = evaluators_config[metric]
        if isinstance(metric_config, BuiltinMetricsConfig):
            deployment_name = get_deployment_name(metric_config.service)
            evaluators[metric] = EvaluatorConfiguration(
                id=evaluator_id.get(metric_config.name.upper()),
                init_params={"deployment_name": deployment_name},
            )
    return evaluators


def get_agent_evaluators(
    evaluators_config: dict[str, Union[BuiltinMetricsConfig, AgentEvalMetricsConfig]],
    azure_openai_endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Prepares agent specific evaluators based on the provided configuration for local evaluation. For local evaluation, evaluators should be in format defined below:
    {
        "metric_name": instance of agent evaluator class, with model_config as parameter
    }
    """
    evaluators = {}
    for metric in evaluators_config:
        metric_config = evaluators_config[metric]
        if isinstance(metric_config, AgentEvalMetricsConfig):
            model_config = get_model_config(metric_config.service, azure_openai_endpoint, api_key)
            evaluators[metric] = agent_evaluators.get(metric.upper())(model_config=model_config)
    return evaluators


def get_model_config(
    service_settings: Union[AzureOpenAIServiceSettings, OpenAIServiceSettings],
    azure_endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
):
    if isinstance(service_settings, AzureOpenAIServiceSettings):
        model_config = AzureOpenAIModelConfiguration(
            azure_deployment=service_settings.deployment_name, azure_endpoint=azure_endpoint
        )
    elif isinstance(service_settings, OpenAIServiceSettings):
        model_config = OpenAIModelConfiguration(
            model=service_settings.model,
            api_key=api_key,
        )

    return model_config


def get_deployment_name(
    service_settings: Union[AzureOpenAIServiceSettings, OpenAIServiceSettings],
) -> str:
    """
    Returns the deployment name based on the service settings.
    """
    if isinstance(service_settings, AzureOpenAIServiceSettings):
        return service_settings.deployment_name
    elif isinstance(service_settings, OpenAIServiceSettings):
        return service_settings.model

    raise ValueError("Unsupported service settings type.")
