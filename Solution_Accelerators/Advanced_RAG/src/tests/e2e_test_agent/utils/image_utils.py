import os
import base64
from copy import deepcopy

def convert_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

def convert_payload_images_to_base64(payload: dict):
    payload_converted = deepcopy(payload)
    for component in payload_converted:
        if component['type'] == 'image':
            # Todo: change this to use blob store
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", component['value'])
            component['value'] = convert_image_to_base64(image_path)
    return payload_converted
        