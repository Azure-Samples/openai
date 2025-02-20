import json
import yaml

def load_file(filepath: str, filetype: str) -> str:
    with open(filepath, "r", encoding='utf-8') as f:
        if filetype == "json":
            return json.load(f)
        elif filetype == "yaml":
            return yaml.safe_load(f)
        else:
            raise Exception(f"Filetype {filetype} not supported")