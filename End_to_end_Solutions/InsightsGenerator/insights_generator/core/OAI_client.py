import requests
import json
import os
import pdb
import tiktoken
import urllib.parse

def is_valid_url(url):
    parsed_url = urllib.parse.urlparse(url)
    return parsed_url.scheme in ["http", "https"] and parsed_url.netloc != ""

def make_prompt_request(prompt, max_tokens = 2048, timeout = 4):
    # Whitelist of allowed URLs
    allowed_urls = ["https://api.openai.com/v1/embeddings", "https://another-trusted-url.com"]
    url = os.getenv("AOAI_ENDPOINT")
    if not is_valid_url(url) or url not in allowed_urls:
        raise ValueError("The provided URL is not allowed.")
    key = os.getenv("AOAI_KEY")
                  
    payload_dict = {"prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "top_p": 0.5,
        "stop": None,
        "best_of": 3
        }
    payload = json.dumps(payload_dict)
    
    authorization_header = key
    
    headers = {
            'api-key': authorization_header,
            'Content-Type': 'application/json'
            }
    
    #pdb.set_trace()
    response = None
    try_count = 0
    while try_count < 4:
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout = timeout)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(e)
            try_count += 1
            continue
        except Exception as e:
            print (e)
            raise Exception(e)
        #print(response.status_code)
        try_count += 1
        if not response is None and response.status_code == 200:
            break
    if not response is None and response.status_code == 200:
        completion = json.loads(response.text)["choices"][0]["text"]
    else:
        completion = None

    return(completion)

def construct_prompt(prompt_parameters, prompt_template):

    # Construct the prompt
    
    prompt = prompt_template.format(**prompt_parameters)
    return(prompt)


def calc_embedding(input_text):

    token_limit = 4000
    encoding_name = "cl100k_base"
    if num_tokens_from_string(input_text, encoding_name) > token_limit:
        print("Num tokens before truncation: " + str(num_tokens_from_string(input_text, encoding_name)))
        input_text = truncate_string(input_text, token_limit, encoding_name)
        print("Num tokens after truncation: " + str(num_tokens_from_string(input_text, encoding_name)))

    #pdb.set_trace()
    url = "https://qnadevoai.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2022-12-01"
    key = os.getenv("AOAI_KEY")
                  
    payload_dict = {"input": input_text}
    #payload_dict = {"input": input_text,
    #    "model": "text-similarity-babbage-001"}
    payload = json.dumps(payload_dict)
    
    
    headers = {
            'api-key': key,
            'Content-Type': 'application/json'
            }
    
    response = None
    #pdb.set_trace()
    try_count = 0
    while try_count < 4:
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout = 5)
        except Exception as e:
            print(e)
        #print(response.status_code)
        try_count += 1
        if not response is None and response.status_code == 200:
            break
        else:
            print("response is:")
            print(response)

    if not response is None and response.status_code == 200:
        embedding = json.loads(response.text)["data"][0]["embedding"]
    else:
        embedding = None

    return(embedding)


# To truncate strings to prevent going over token

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def truncate_string(string, token_limit, encoding_name):

    # TODO: Should we use delim '.' instead?
    #     Optimize by splitting on delim, instead of current logic.
    #     We may end up with trailing delim. Remove?

    trunc_str_len = len(string)
    while num_tokens_from_string(string[:trunc_str_len], encoding_name) > token_limit:
        trunc_str_len -= 1
        while string[(trunc_str_len - 1)] != " ":
            trunc_str_len -= 1

    return(string[:trunc_str_len])


