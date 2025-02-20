import json
import os

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from flows.flow import Flow
from promptflow.client import load_flow
from utils.data_loader import get_tone_eval_data
from utils.response_utils import safe_load_json


class CheckTable:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        check_table_prompty_path = os.path.join(current_dir, "..", "static", "check_table.prompty")
        self._flow = load_flow(check_table_prompty_path, model={"configuration": model_config})
    
    def __call__(self, *, text: str, **kwargs):
        llm_response = self._flow(text=text)
        try:
            response = safe_load_json(llm_response)
        except Exception as ex:
            print(f"Error parsing llm response: {ex}")
            response = llm_response
        return response

class CompareTone:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        tone_prompty_path = os.path.join(current_dir, "..", "static", "tone.prompty")
        self._flow = load_flow(tone_prompty_path, model={"configuration": model_config})
    
    def __call__(self, *, text_1: str, text_2: str, **kwargs):
        llm_response = self._flow(text_1=text_1, text_2=text_2)
        try:
            response = safe_load_json(llm_response)
        except Exception as ex:
            print(f"Error parsing llm response: {ex}")
            response = llm_response
        return response

class ToneEvalFlow(Flow):
    def __init__(self, model_config, params):
        super().__init__()
        self._check_table = CheckTable(model_config)
        self._compare_tone = CompareTone(model_config)
        self._params = params
        self._data = []
        self._results_root_dir = params.save_path
    
    def load_data(self):
        azure_credential = DefaultAzureCredential()
        aml_client = MLClient(azure_credential, self._params.subscription_id, self._params.resource_group, self._params.workspace)
        self._data = get_tone_eval_data(self._params, aml_client)

    def evaluate(self):
        self.load_data()
        evaluation_results = list()
        for data in self._data:
            check_table_response = self._check_table(text=data['fine_tuned_answer'])
            tone_response = self._compare_tone(text_1=data['fine_tuned_answer'], text_2=data['control_answer'])
            evaluation_results.append({"has_table": check_table_response['Table'],
                                       "tone_judgement": tone_response['Judgement'],
                                       "tone_judgement_reason": tone_response['Reason']})
        self._save_results(evaluation_results, "evaluation_results.json")
        self.aggregate_results(evaluation_results)
    
    def aggregate_results(self, results):
        has_table_count = 0
        tone_judgement_count = 0
        for result in results:
            if result['has_table'].lower() == "true":
                has_table_count += 1
            if result['tone_judgement'].lower() == "TEXT_1".lower():
                tone_judgement_count += 1
        self._save_results({"has_table_count": has_table_count, 
                            "tone_judgement_count": tone_judgement_count,
                            "total_count": len(results)}, "aggregate_results.json")
    
    def _save_results(self, results, file_name: str):
        file_path = os.path.join(self._results_root_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Evaluation results saved to {file_path}")
        