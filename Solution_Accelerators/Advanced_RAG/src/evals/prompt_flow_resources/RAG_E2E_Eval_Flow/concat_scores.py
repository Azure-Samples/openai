from promptflow import tool
import numpy as np
import re
import json

@tool
def concat_results(similarity_score: str, difficulty: str):

    load_list = [{
        "name": "gpt_similarity",
        "difficulty": difficulty,
        "score_info": similarity_score,
    }]
    score_list = []
    errors = []
    for item in load_list:
        try:
            print(item["score_info"])
            score_info = json.loads(item["score_info"])
            print(score_info)

            score = score_info["grade"]
            comment = score_info["comment"]
            # match = re.search(r"\d", score)
            # if match:
            #     score = match.group()
            # score = float(score)
        except Exception as e:
            score = np.nan
            comment = ""
            errors.append({"name": item["name"], "msg":   str(e), "data": item["score_info"]})
        
        score_list.append({
            "name": item["name"],
            "score": score,
            "comment": comment,
            "difficulty": item["difficulty"]
        })

    variant_level_result = {}
    for item in score_list:
        item_name = str(item["name"])

        # Overall Score
        variant_level_result[item_name] = item["score"]
        variant_level_result[item_name + "_pass_rate"] = 1 if item["score"] >= 4 else 0

        # Difficulty Score
        current_difficulty = item["difficulty"].lower()
        metric_name = f"{item_name}_{current_difficulty}"
        variant_level_result[metric_name] = item["score"]
        variant_level_result["comment"] = item["comment"]
        variant_level_result[metric_name + "_pass_rate"] = 1 if item["score"] >= 4 else 0
        
    return variant_level_result
