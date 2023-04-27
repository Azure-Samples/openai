import copy

def parse_review(review):
    parsed_review = copy.copy(review)
    review_text = parsed_review["review_text"]
    comments = review_text.split("\n")
    parsed_review_text = {}
    maxsplit = 1
    for comment in comments:
        if not ":" in comment:
            continue
        try:
            comment_number, comment_text = comment.split(":", maxsplit)
            comment_number = comment_number.strip()
            comment_text = comment_text.strip()
            parsed_review_text[comment_number] = comment_text
        except:
            print("Exception in parsing review text")
            print(comment)
    parsed_review["parsed_review_text"] = parsed_review_text
    return(parsed_review)

def parse_reviews(reviews):
    """Generate parsed version of the text corpus. This will be used for generating references.
    
    Currently, we expect the texts to be of the form:
    1. Delimited by \n
    2. Prefixed by line number (unique across entire corpus), Followed by : and then the text of that line
    This is parsed into a dict. Keys are the line numbers and values are the text of that line.
    This is used to look up references.
    
    :param reviews: The text corpus as a list. Each entry in the list is a dict.
        Each dict must have the key 'review_text', which stores the individual text
    :type reviews: list
    :returns: Text corpus as a list. With the additional key 'parsed_review_text' in each entry.
    :rtype: list
    """
    
    parsed_reviews = []
    for review in reviews:
        parsed_review = parse_review(review)
        parsed_reviews.append(parsed_review)
        
    return(parsed_reviews)