from . import extract_sentiment_aspects

async def get_per_review_aspects(project_object, reviews, batch_size):
    """Get aspects + sentiments from the text corpus.
    
    Aspects are the topics discussed in the corpus. We use the terms aspects and topics interchangeably.
    The text corpus is contained in the reviews parameter.
    The individual texts are batched in groups of batch_size.
    Aspects and corresponding sentiments are extracted for each batch. 
    Aspects, sentiments are extracted as key value pairs of type (aspect, sentiment). eg (comfort, positive).
    
    Aspects and sentiments are extracted at batch level for two reasons:
    1. Extracting aspects from the entire corpus at once (in one prompt) gives poor results.
        Aspects can be missed. Also, there is no numerical score of the realtive frequency of aspects in the corpus.
        Further, the corpus may be too large to fit into a single prompt.
    2. Extracting aspects from the individual texts (batch_size = 1), can give inconsistent naming of 
        aspects across the corpus. Batching helps with this.
    
    :param project_object: metadata of the project
    :param reviews: The text corpus as a list. Each entry in the list is a dict.
        Each dict must have the key 'review_text', which stores the individual text
    :batch_size: The size of the batch
    :type project_name: dict
    :type reviews: list
    :type batch_size: int
    :returns: list of dicts. Each dict has keys: "sentiment_aspects", "review_text".
        review_text will contain the batched text. ie all individual texts in the batch, combined.
        sentiment_aspects is a list of tuples. Each tuple is of form (aspect, sentiment).
    :rtype: list
    """

    # Extract sentiment aspects from the reviews
    product_category = project_object["productCategory"]
    product_name = project_object["productName"]
    reviews_with_sentiment_aspects = extract_sentiment_aspects.extract_sentiment_aspects(reviews, product_name, batch_size)

    return(reviews_with_sentiment_aspects)
