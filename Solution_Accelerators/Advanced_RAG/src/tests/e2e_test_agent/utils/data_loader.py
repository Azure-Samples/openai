from copy import deepcopy
from collections import defaultdict
from utils.files import load_file

def reorganize_data(yaml_data):
    conversation_dict = defaultdict(list)
    for item in yaml_data:
        conversation_id = item['conversation_id']
        if conversation_id not in conversation_dict.keys():
            conversation_dict[conversation_id] = list()
        conversation_dict[conversation_id].append(deepcopy(item))
    return dict(conversation_dict)

def load_data(filepath: str) -> dict:
    yaml_data = load_file(filepath, "yaml")
    return reorganize_data(yaml_data)