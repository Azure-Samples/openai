import tiktoken
from backend.config import DefaultConfig
from typing import List, Optional

convert_history_to_text = lambda lst: ' '.join(f"{key}: {value}" for conversation in lst for key, value in conversation.items())
combine_index = lambda idx_lst: ' '.join(idx_lst)


def compute_tokens(input_str: str, model_name: Optional[str] = "gpt-4") -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(input_str))


def trim_history(history: List[dict], max_token_length: int, model_name: Optional[str] = "gpt-4") -> List[dict]:
    if len(history) == 0:
        return history
    
    encoding = tiktoken.encoding_for_model(model_name)
    current_token_length = len(encoding.encode(convert_history_to_text(history)))

    while current_token_length > max_token_length:
        # Remove the oldest conversation, first element containing user query and second element containing assistant response
        history = history[2:]
        current_token_length = len(encoding.encode(convert_history_to_text(history)))    
    
    return history


def trim_history_and_index_combined(history: List[dict], index: List, max_token_length: int, model_name: Optional[str] = "gpt-4") -> List[dict]:
    # start trimming from index first
    trimming_idx = 1
    
    encoding = tiktoken.encoding_for_model(model_name)
    current_token_length = len(encoding.encode(convert_history_to_text(history) + combine_index(index)))

    while current_token_length > max_token_length:
        # Index is ranking based on relevance, remove the last element (least relevant)
        if len(index) and trimming_idx % (DefaultConfig.RATIO_OF_INDEX_TO_HISTORY + 1) != 0:
            index.pop()
        # Remove the oldest conversation, first element containing user query and second element containing assistant response
        elif len(history):
            history = history[2:]
        current_token_length = len(encoding.encode(convert_history_to_text(history) + combine_index(index)))

        trimming_idx += 1
    
    return history, index