# import module
from . import OAI_client
import re
import datetime

def classify_nl_query(nl_query):
    
    prompt_template_filename = "insights_generator/core/prompt_template_classify_query.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template_summary = prompt_template_file.read()
    
    prompt_parameters = {"nl_query" : nl_query}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template_summary)
    if prompt[-1] == "\n":
        prompt = prompt[:-1] # To get rid of trailing newline

    completion = OAI_client.make_prompt_request(prompt, max_tokens = 200, timeout = 10)
    completion = completion.split("\n")[0]

    nl_query_type = completion

    return nl_query_type

# Get search query for the NL question
# This is the filter only version
def get_search_query_filter(question, top_aspects):
    
    prompt_template_filename = "insights_generator/core/prompt_template_prepare_query.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template_summary = prompt_template_file.read()
    
    prompt_parameters = {"question" : question, "top_aspects": top_aspects}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template_summary)

    completion = OAI_client.make_prompt_request(prompt, max_tokens = 200, timeout = 10)
    completion_lines = completion.split("\n")

    aspect = None
    sentiment = None
    recency = None
    for completion_line in completion_lines:
        completion_line = completion_line.lower()
        if "1." in completion_line:
            for top_aspect in top_aspects:
                if top_aspect in completion_line.lower( ):
                    aspect = top_aspect
        elif "2." in completion_line:
            if "negative" in completion_line.lower( ):
                sentiment = "negative"
            elif "positive" in completion_line.lower( ):
                sentiment = "positive"
        elif "3." in completion_line:
            recency = completion_line.strip( ).lower( )

    aspect_sentiment = None
    if (not aspect is None) and (not sentiment is None):
        aspect_sentiment = aspect + "_" + sentiment
    cutoff_date = None
    if not recency is None:
        current_date = datetime.datetime.now()
        recency_quantity = re.compile("\d+").findall(recency)
        if recency_quantity:
            recency_quantity = int(recency_quantity[0])
            if "months" in recency:
                offset = datetime.timedelta(days = 30 * recency_quantity)
            if "year" in recency:
                offset = datetime.timedelta(days = 365 * recency_quantity)
            cutoff_date = current_date - offset
            cutoff_date = cutoff_date.strftime('%Y-%m-%d') + "T00:00:00Z"

    return {"aspect_sentiment": aspect_sentiment, "cutoff_date": cutoff_date}
