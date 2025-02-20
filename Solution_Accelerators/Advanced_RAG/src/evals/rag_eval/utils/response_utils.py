import json


def safe_load_json(input_data):
    if isinstance(input_data, dict):
        return input_data
    elif isinstance(input_data, str):
        try:
            return json.loads(input_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string provided.")
    else:
        raise TypeError("Input must be a dictionary or a JSON string.")