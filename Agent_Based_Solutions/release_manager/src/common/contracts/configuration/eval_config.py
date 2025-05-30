# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from common.contracts.configuration.config_base import ConfigBase
from common.contracts.configuration.config_type import ConfigType

from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, Union

"""
Instructions for using eval_config.py:

1. Dataset Configuration:
   - Use `aml_dataset` to specify the Azure Machine Learning dataset.
   - Use `local_dataset` to specify a local dataset.
   - Only one of `aml_dataset` or `local_dataset` should be provided. Providing both will raise a validation error.

2. Metric Configuration:
   - Define metrics using `BuiltinMetricsConfig`. Builtin metrics include metrics provided at Evaluator Library on Foundry.
   - `BuiltinMetricsConfig` requires a `name` and an optional `service` configuration.

3. Agent Evaluation:
   - Use `AgentEvaluation` for agent-specific evaluation.
   - Provide either `agent_config_id` or `agent_id`, but not both.
   - Optionally, specify `config_file_path` for additional configuration. If provided will use file to get configuration for agents and services.
     Otherwise will use config endpoint to get the configuration.

4. End-to-End Evaluation:
   - Use `EndToEndEvaluation` for holistic evaluation without agent-specific details.

5. Evaluation Job Configuration:
   - Use `EvaluationJobConfig` to define evaluation jobs.
   - Set `config_type` to `ConfigType.EVALUATION.value`.
   - Use `config_body` to specify the evaluation configuration (`AgentEvaluation` or `EndToEndEvaluation`).

6. Evaluations Configuration:
   - Use `EvaluationsConfig` to define a collection of evaluation jobs.

Example:
    evaluation_jobs:
        evaluation_1:
            config_body:
            type: AgentEvaluation
            agent_config_id: agent_20250418_217444
            service_config_id: service_20250418_579029
            aml_dataset: MS_Eval_Dataset
            metric_config:
                similarity:
                name: "similarity"
                service:
                    llm_service: "AzureOpenAI"
                    deployment_name: "gpt-4o-2"
                relevance:
                name: "relevance"
                service:
                    llm_service:  "AzureOpenAI"
                    deployment_name: "gpt-4o-2"
"""

class ServiceName(str, Enum):
    OPENAI = "OpenAI"
    AZURE_OPENAI = "AzureOpenAI"

class ServiceSettings(BaseModel):
    llm_service: ServiceName

class AzureOpenAIServiceSettings(ServiceSettings):
    deployment_name: str

class OpenAIServiceSettings(ServiceSettings):
    model: str

class BuiltinMetricsConfig(BaseModel):
    name: str
    service: Optional[Union[AzureOpenAIServiceSettings, OpenAIServiceSettings]]
    type: Literal["BuiltInMetricsConfig"] = "BuiltInMetricsConfig"

class AgentEvalMetricsConfig(BaseModel):
    name: str
    service: Optional[Union[AzureOpenAIServiceSettings, OpenAIServiceSettings]]
    type: Literal["AgentEvaluatorConfig"] = "AgentEvaluatorConfig"

class CustomMetricConfig(BaseModel):
    name: str
    service: Optional[Union[AzureOpenAIServiceSettings, OpenAIServiceSettings]]
    prompt: str
    type: Literal["CustomMetricConfig"] = "CustomMetricConfig"

class BaseEvaluationConfig(BaseModel):
    aml_dataset: Optional[str] = None
    local_dataset: Optional[str] = None
    use_cached_dataset: bool = Field(default=False)
    metric_config: dict[str, Union[BuiltinMetricsConfig, AgentEvalMetricsConfig, CustomMetricConfig]]

    @model_validator(mode="before")
    def validate_dataset(cls, values):
        """
        Validate the dataset to ensure only one of aml_dataset or local_dataset is provided.
        """
        aml_dataset = values.get("aml_dataset")
        local_dataset = values.get("local_dataset")
        if aml_dataset and local_dataset:
            raise ValueError("Only one of aml_dataset or local_dataset should be provided.")
        return values

class AgentEvaluation(BaseEvaluationConfig):
    type: Literal["AgentEvaluation"] = "AgentEvaluation"
    agent_config_id: Optional[str] = None
    agent_id: Optional[str] = None
    service_config_id: Optional[str] = None
    config_file_path: Optional[str] = None

    @model_validator(mode="before")
    def validate(cls, values):
        """
        Validate to ensure only one of agent_config_id or agent_id is provided.
        If agent_config_id is provided, service_config_id must also be provided.
        """
        agent_config_id = values.get("agent_config_id")
        agent_id = values.get("agent_id")
        if agent_config_id and agent_id:
            raise ValueError("Only one of agent_config_id or agent_id should be provided.")
        if not values.get("service_config_id") and not values.get("config_file_path"):
            raise ValueError("Please provide service_config_id.")
        return values

class EndToEndEvaluation(BaseEvaluationConfig):
    type: Literal["EndToEndEvaluation"] = "EndToEndEvaluation"

EvaluationConfigUnion = Union[AgentEvaluation, EndToEndEvaluation]

class EvaluationJobConfig(ConfigBase):
    """
    EvaluationConfig is a configuration class that inherits from ConfigBase. It represents
    the configuration details specific to an evaluation job.

    Attributes:
        config_type (str): A string representing the type of configuration.
            Defaults to the value of `ConfigType.EVALUATION.value`.
        config_body (EvaluationConfigUnion): The body of the eval configuration,
            which can be one of the types defined in the EvalConfigUnion.
    """
    config_type: str = ConfigType.EVALUATION.value
    config_body: EvaluationConfigUnion

class EvaluationsConfig(BaseModel):
    """
    EvaluationsConfig is a configuration class that represents the configuration details
    for evaluations. It contains a list of evaluation jobs.

    Attributes:
        evaluation_jobs (list[EvalJobConfig]): A list of evaluation job configurations.
    """
    evaluation_jobs: dict[str, EvaluationJobConfig]