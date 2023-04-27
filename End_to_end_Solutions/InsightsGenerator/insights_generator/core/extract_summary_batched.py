from . import OAI_client
from joblib import Parallel, delayed

def summarize_review(review):
    prompt_template = """{review_text}
    
tl;dr"""
    
    prompt_parameters = {
            "review_text" : review["review_text"]
            }
    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
    timeout = 5
    completion = OAI_client.make_prompt_request(prompt, timeout = timeout)
    
    return(completion)

def summarize_reviews(reviews):
    """Summarizes a text corpus in a batched manner
    
    Given a corpus of text documents, produces an overall summary.
    The corpus consists of a list of individual texts.
    Summary of each individual text is done, then these summaries are
    combined into an overall summary.
    
    Summarization is done in this batched manner for two reasons:
    1. To support corpus that is too large for a single prompt
    2. To provide a summary for each text in the corpus. This provides a more nuanced set of summaries
        which are a check against omission of topics in the overall summary.
        
    :param reviews: The text corpus as a list. Each entry in the list is a dict.
        Each dict must have the key 'review_text', which stores the individual text
    :type reviews: list
    :returns: Overall summary in a few lines
    :rtype: string
    """
    
    # Get per review summaries
    # 
    print("Summarize each chunk of the chat")
    n_jobs = 4
    print("Starting " + str(n_jobs) + " parallel jobs.")
    completions = Parallel(n_jobs = n_jobs)(delayed(summarize_review)(review) for review in reviews)
    print("Done")
    
    summaries = []
    for completion in completions:
        if not completion is None:
            summaries.append(completion)
            
            
    # Get overall summary
    prompt_template = """{summaries}
    
    tl;dr"""
    
    prompt_parameters = {
            "summaries" : "\n".join(summaries)
            }
    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
    #print(prompt)
    timeout = 5
    overall_summary = OAI_client.make_prompt_request(prompt, timeout = timeout)
    
    return(overall_summary, summaries)
