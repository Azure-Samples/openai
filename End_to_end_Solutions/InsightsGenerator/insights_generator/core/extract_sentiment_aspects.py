from . import OAI_client
from joblib import Parallel, delayed
import time
import itertools
import pdb

def extract_sentiment_aspects_for_batch(reviews_batch, product_name, prompt_template):

    reviews_batch_text = [review["review_text"] for review in reviews_batch]
    reviews_batch_text = "review: " + "\nreview: ".join(reviews_batch_text)
    sentiment_aspects = None
    results = {"review_text" : reviews_batch_text,
            "sentiment_aspects" : sentiment_aspects
            }
    prompt_parameters = {"reviews_batch_text" : reviews_batch_text,
            "product_name" : product_name}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
    #print(prompt)
    completion = OAI_client.make_prompt_request(prompt)

    if completion is None:
        return(results)

    sentiment_aspects = []
    # completion is of the form:
    # "Comfort : Positive, Sound Quality : Positive, Noise Cancellation : Positive, ANC : Positive."
    # Split on , to get individual sentiment aspect
    try:
        sentiment_aspects_for_batch = completion.split(",")
        for y in sentiment_aspects_for_batch:
            aspect, sentiment = y.split(":")
            aspect = aspect.lower().strip()
            sentiment = sentiment.lower().strip()
            sentiment_aspects.append((aspect, sentiment))
    except:
        print("Trouble parsing: " + completion)
        pass

    results["sentiment_aspects"] = sentiment_aspects

    return(results)


def batched(iterable, n):
    # taken from itertools recipies
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := tuple(itertools.islice(it, n))):
        yield batch

def calc_review_batches(reviews, batch_size):
    batched_reviews = list(batched(reviews, batch_size))
    return(batched_reviews)

def extract_sentiment_aspects(reviews, product_name, batch_size):

    prompt_template_filename = "insights_generator/core/prompt_template_key_value.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template_key_value = prompt_template_file.read()

    batched_reviews = calc_review_batches(reviews, batch_size)

    n_jobs = 4
    print("Extracting sentiment aspects for {} reviews".format(len(reviews)))
    print("Starting {} parallel extractors".format(n_jobs))
    start_time = time.time()
    num_successful_extractions_NL = 0
    num_successful_extractions_key_value = 0
    results = Parallel(n_jobs = n_jobs)(delayed(extract_sentiment_aspects_for_batch)(reviews_batch, product_name, prompt_template_key_value) for reviews_batch in batched_reviews)
    stop_time = time.time()
    elapsed_time = stop_time - start_time
    print("Extracted sentiment aspects for {} reviews in {} seconds".format(len(reviews), elapsed_time))
    print("Done.")

    return(results)
