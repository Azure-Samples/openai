import re
from . import OAI_client
from collections import defaultdict
from . import extract_sentiment_aspects_batched
from ..clients.storage_client import StorageClient

def parse_the_sentiment_aspects_key_value(reviews_with_sentiment_aspects):

    sentiment_aspects = []
    for review in reviews_with_sentiment_aspects:
        for sentiment_aspect in review["sentiment_aspects_key_value"]:
            pattern = re.compile("- *(.*): *(.*)")
            result = pattern.search(sentiment_aspect)
            if not result is None:
                aspect = result.group(1).lower()
                sentiment = result.group(2).lower()
                sentiment_aspects.append((aspect, sentiment))

    return(sentiment_aspects)

def extract_top_tags_inner(sentiment_aspects):

    num_top_tags = 10

    prompt_template_filename = "insights_generator/core/prompt_template_extract_top_tags.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template_summary = prompt_template_file.read()

    sentiment_aspects = [x["sentiment_aspects"] for x in sentiment_aspects]
    prompt_parameters = {"sentiment_aspects" : "\n".join(sentiment_aspects),
            "num_top_tags" : num_top_tags}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template_summary)

    completion = OAI_client.make_prompt_request(prompt, max_tokens = 200, timeout = 10)
    completion_lines = completion.split("\n")
    print("Extracted top tags")

    # Parse 
    top_tags = []
    for line in completion_lines:
        if len(line) > 0  and line[0] == "-":
            top_tags.append(line[1:])

    if len(top_tags) > num_top_tags:
        top_tags = top_tags[:num_top_tags]

    return top_tags

def extract_top_tags(reviews_batches_with_sentiment_aspects):

    sentiment_aspects = []
    for x in reviews_batches_with_sentiment_aspects:
        if not x["sentiment_aspects"] is None:
            sentiment_aspects.extend(x["sentiment_aspects"])

    # Get counts by aspect
    aspect_counts = defaultdict(int)
    for aspect, sentiment in sentiment_aspects:
        aspect_counts[aspect] += 1
    aspect_counts = list(aspect_counts.items())
    aspect_counts.sort(key = lambda x: -x[1])
    if len(aspect_counts) > 10:
        aspect_counts = aspect_counts[:10]
    aspects, counts = zip(*aspect_counts)

    return(aspects, counts)

async def get_top_aspects_from_sentiment_aspects(project_object, reviews_with_sentiment_aspects):
    """Get the top aspects
    
    We use the terms aspects and topics interchangeably.
    Given the aspects for each batch of reviews,
    get the aspects that occur the most across the corpus.
    1. The frequency of each aspect across batches is calculated as a frequency score.
    2. We retain the top 10 aspects (most frequent).

    
    :param project_object: metadata of the project
    :param reviews_with_sentiment_aspects: list of reviews (possibly batched) with aspects information
    :type project_name: str
    :type reviews_with_sentiment_aspects: list
    :returns: list of aspects and list of corresponding frequencies.
        aspects are strings, counts are ints.
    :rtype: tuple of 2 lists.    
    """

    # Extract top aspects
    top_aspects, top_aspects_counts = extract_top_tags(reviews_with_sentiment_aspects)

    # Store top aspects in project metadata, used later.
    project_object["top_aspects"] = top_aspects

    return(project_object, top_aspects, top_aspects_counts)


async def get_top_aspects_from_reviews(project_object, reviews):
    """Gets the top aspects from the text corpus.
    
    We use the terms aspects and topics interchangeably.
    1. The individual texts are batched.
    2. Aspects are extracted for each batch.
    3. The frequency of each aspect across batches is calculated as a frequency score.
    4. We retain the top 10 aspects (most frequent).
    
    :param project_object: metadata of the project
    :param reviews: The text corpus as a list. Each entry in the list is a dict.
        Each dict must have the key 'review_text', which stores the individual text
    :type project_name: str
    :type reviews: list
    :returns: list of aspects and list of corresponding frequencies.
        aspects are strings, counts are ints.
    :rtype: tuple of 2 lists.
    """
    # Get per review aspects
    batch_size = 1
    reviews_with_sentiment_aspects = await extract_sentiment_aspects_batched.get_per_review_aspects(project_object, reviews, batch_size)

    # Get the top aspects
    project_object, top_aspects, top_aspects_counts = await get_top_aspects_from_sentiment_aspects(project_object, reviews_with_sentiment_aspects)
    
    return(project_object, top_aspects, top_aspects_counts)
