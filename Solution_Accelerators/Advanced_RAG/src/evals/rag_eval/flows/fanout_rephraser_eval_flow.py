import ast
import json
import os
import re

from azure.ai.evaluation import SimilarityEvaluator
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from flows.flow import Flow
from promptflow.client import load_flow
from utils.data_loader import get_rephraser_questions
from utils.response_utils import safe_load_json


class Rephraser:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        tone_prompty_path = os.path.join(current_dir, "..", "static", "rephrase.prompty")
        self._flow = load_flow(tone_prompty_path, model={"configuration": model_config})

    def __call__(self, *, question: str, **kwargs):
        llm_response = self._flow(question=question)
        try:
            response = safe_load_json(llm_response)
        except Exception as ex:
            print(f"Error parsing LLM response: {ex}")
            response = llm_response
        return response


class FanoutRephraserEvaluationFlow(Flow):
    def __init__(self, model_config, params):
        super().__init__()
        self._rephraser = Rephraser(model_config)
        self._gpt_similarity_evaluator = SimilarityEvaluator(model_config)
        self._params = params
        self._conversations = []
        self._results_root_dir = params.save_path
    
    def load_data(self):
        azure_credential = DefaultAzureCredential()
        aml_client = MLClient(azure_credential, self._params.subscription_id, self._params.resource_group, self._params.workspace)
        self._conversations = get_rephraser_questions(self._params, aml_client)

    def evaluate(self):
        self.load_data()
        evaluation_results = list()
        for idx, history in enumerate(self._conversations[:20]):
            print(f"Processing conversation {idx} of {len(self._conversations)}")
            user_message = "Here's the history" + history[0]['user'].split("Here's the history")[1]
            rephraser_response = self._rephraser(question=user_message)

            parsed_query = self._parse_rephrased_query(rephraser_response)
            ground_truth = ast.literal_eval(history[1]['assistant'])

            metrics = self._get_metrics(
                [ground_truth.get('search_requests', [])],
                [parsed_query.get('search_requests', [])]
            )

            gpt_similarity_data = self._generate_gpt_similarity(ground_truth, parsed_query, user_message)
            similarity = self._gpt_similarity_evaluator(
                query=gpt_similarity_data['question'],
                response=gpt_similarity_data['prediction'],
                ground_truth=gpt_similarity_data['groundtruth']
            )
            evaluation_results.append({"user_message": user_message, 
                                       "rephraser_response": parsed_query, 
                                       "ground_truth": ground_truth, 
                                       "metrics": metrics, 
                                       "similarity": similarity})
            
        
        self._save_results(evaluation_results, "evaluation_results.json")
        self.aggregate_results(evaluation_results)
    
    def aggregate_results(self, evaluation_results):
        similarity_scores = [result['similarity']['gpt_similarity'] for result in evaluation_results]
        count = len(similarity_scores)
        avg_similarity = sum(similarity_scores) / count if count > 0 else 1
        self._save_results({"avg_similarity": avg_similarity, "count": count}, "aggregated_results.json")

    @staticmethod
    def _parse_rephrased_query(search_metadata: dict):
        """
        Extracts and normalizes search requests from the JSON-like structure.
        """
        output = {"search_requests": []}
        for request in search_metadata.get("search_requests", []):
            # Handle subsidiary_filter
            subsidiary = request.get("subsidiary_filter")
            if subsidiary is not None:
                subsidiary = subsidiary.replace("Abu Dhabi", "Alpha Dhabi")

            # Handle earliest_year_filter
            raw_year = request.get("earliest_year_filter", 0) or 0
            if isinstance(raw_year, int):
                year = raw_year
            else:
                # Attempt to parse non-integer year
                try:
                    year = int(raw_year)
                except ValueError:
                    match = re.search(r"\b2022\b", str(raw_year))
                    year = int(match.group()) if match else None

            output["search_requests"].append({
                "search_query": request.get("search_query"),
                "subsidiary_filter": subsidiary,
                "financial_term": request.get("financial_term"),
                "earliest_year_filter": year,
            })
        return output

    @staticmethod
    def _get_metrics(true_output, pred_output):
        correct_counts = []
        subsidiary_accs, year_accs, fin_term_accs = [], [], []

        for true_q, pred_q in zip(true_output, pred_output):
            correct_counts.append(len(true_q) == len(pred_q))

            true_fin_term = {x['financial_term'] for x in true_q}
            pred_fin_term = {x['financial_term'] for x in pred_q}
            true_subsidiary = {x['subsidiary_filter'] for x in true_q}
            pred_subsidiary = {x['subsidiary_filter'] for x in pred_q}
            true_years = {x['earliest_year_filter'] for x in true_q}
            pred_years = {x['earliest_year_filter'] for x in pred_q}

            subsidiary_accs.append(
                len(true_subsidiary.intersection(pred_subsidiary)) / len(true_subsidiary)
                if true_subsidiary else 1.0
            )
            year_accs.append(
                len(true_years.intersection(pred_years)) / len(true_years)
                if true_years else 1.0
            )
            fin_term_accs.append(
                len(true_fin_term.intersection(pred_fin_term)) / len(true_fin_term)
                if true_fin_term else 1.0
            )

        return {
            "correct_count_accuracy": sum(correct_counts) / len(correct_counts) if correct_counts else 0,
            "avg_subsidiary_accuracy": sum(subsidiary_accs) / len(subsidiary_accs) if subsidiary_accs else 0,
            "avg_year_accuracy": sum(year_accs) / len(year_accs) if year_accs else 0,
            "avg_fin_term_accuracy": sum(fin_term_accs) / len(fin_term_accs) if fin_term_accs else 0,
            "min_subsidiary_accuracy": min(subsidiary_accs) if subsidiary_accs else 0,
            "max_subsidiary_accuracy": max(subsidiary_accs) if subsidiary_accs else 0,
            "min_year_accuracy": min(year_accs) if year_accs else 0,
            "max_year_accuracy": max(year_accs) if year_accs else 0,
            "min_fin_term_accuracy": min(fin_term_accs) if fin_term_accs else 0,
            "max_fin_term_accuracy": max(fin_term_accs) if fin_term_accs else 0,
        }

    @staticmethod
    def _generate_gpt_similarity(groundtruth, prediction, question):
        output_question = (
            "\nRephrase the following question so it is clear and unambiguous. "
            "Use the history to build your questions.\n" + question
        )
        output_groundtruth = "\n".join(
            f"- {query['search_query']}" for query in groundtruth["search_requests"]
        )
        output_prediction = "\n".join(
            f"- {query['search_query']}" for query in prediction["search_requests"]
        )

        return {
            "question": output_question,
            "groundtruth": output_groundtruth,
            "prediction": output_prediction,
        }

    def _save_results(self, results, file_name: str):
        file_path = os.path.join(self._results_root_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Evaluation results saved to {file_path}")
