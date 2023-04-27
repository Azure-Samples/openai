import re
from sklearn.metrics.pairwise import cosine_similarity
from . import OAI_client
from joblib import Parallel, delayed
import random
import json
import pdb
from collections import defaultdict
from joblib import Parallel, delayed

def extract_top_aspects_for_review(review, top_aspects_string, product_category, prompt_template):

    # Make the prompt
    prompt_parameters = {
            "product_category" : product_category,
            "review_text" : review["review_text"],
            "top_aspects" : top_aspects_string
            }
    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
    # Fire the request
    completion = OAI_client.make_prompt_request(prompt)
    # Parse the completion
    review["top_aspect_sentiments"] = None
    if completion is None:
        return(review)
    try:
        sentiment_aspects_for_review = {}
        completion = completion.split(",")
        for y in completion:
            aspect, sentiment = y.split(":")
            aspect = aspect.lower().strip()
            sentiment = sentiment.lower().strip()
            sentiment_aspects_for_review[aspect] = sentiment
        review["top_aspect_sentiments"] = sentiment_aspects_for_review
    except:
        pass

    return(review)

def extract_statistical_summary(product_category, reviews, top_aspects, skip_aspect_summaries = False):


    # Extract top aspects for each review
    top_aspects_string = ",".join(top_aspects)

    prompt_template_filename = "insights_generator/core/prompt_template_per_review_top_aspects.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template = prompt_template_file.read()

    n_jobs = 4
    reviews = Parallel(n_jobs = n_jobs)(delayed(extract_top_aspects_for_review)(review, top_aspects_string, product_category, prompt_template) for review in reviews)

    # Overall statistics
    overall_statistics_dict = calculate_overall_statistics(reviews, top_aspects)
    overall_statistics_dict = extract_top_aspects_overall_sentiment(overall_statistics_dict)

    if not skip_aspect_summaries:
        # Aspect based summary
        reviews, overall_statistics_dict = extract_keyphrases_for_top_aspects(product_category, reviews, top_aspects, overall_statistics_dict)
        overall_statistics_dict = extract_aspect_summaries(overall_statistics_dict)

    print("Extracted all statistics")
    
    return(reviews, overall_statistics_dict)

def calculate_overall_statistics(reviews, top_aspects):

    overall_statistics_dict = {}
    for aspect in top_aspects:
        overall_statistics_dict[aspect] = defaultdict(int)

    for review in reviews:
        top_aspect_sentiments = review["top_aspect_sentiments"]
        if top_aspect_sentiments is None:
            continue
        for aspect, sentiment in top_aspect_sentiments.items():
            # There may be some aspects in reviews, which are not in top_aspects
            # since the latter is truncated to top 10. Hence the if
            if aspect in overall_statistics_dict:
                overall_statistics_dict[aspect][sentiment] += 1

    return(overall_statistics_dict)

def calculate_overall_statistics_for_azure_search(reviews, top_aspects):

    overall_statistics_dict = {}
    for aspect in top_aspects:
        overall_statistics_dict[aspect] = {"positive" : 0, "negative" : 0, "unmentioned":0}

    for review in reviews:
        top_aspect_sentiments = review["top_aspect_sentiments"]
        for x in top_aspect_sentiments:
            aspect = x["aspect"]
            sentiment = x["sentiment"]
            overall_statistics_dict[aspect][sentiment] += 1

    return(overall_statistics_dict)


def extract_top_aspects_overall_sentiment(overall_statistics_dict):
    # For each top aspect, extract an overall sentiment (ie across all reviews)

    for aspect, statistics in overall_statistics_dict.items():
        overall_statistics_dict[aspect]["overall_sentiment"] = None
        overall_statistics_dict[aspect]["percentage_positive"] = None
        num_positive = statistics["positive"]
        num_negative = statistics["negative"]
        num_total = num_positive + num_negative
        if num_total >= 5:
            percentage_positive = 100.0 * num_positive / num_total
            overall_statistics_dict[aspect]["percentage_positive"] = percentage_positive
            if percentage_positive > 75:
                overall_statistics_dict[aspect]["overall_sentiment"] = "positive"
            elif percentage_positive < 25:
                overall_statistics_dict[aspect]["overall_sentiment"] = "negative"

    return(overall_statistics_dict)

def lcs_match_y(x, y):

    # Match percentage is len of longest common substring as percentage of len y
    lcs_len = pylcs.lcs_string_length(x, y)
    if len(y) > 0:
        match_percentage = 100 * lcs_len / len(y)
    else:
        match_percentage = 0

    return(match_percentage)

def loosely_contains(x, y, match_mode = "any"):

    # Does x loosely contain y

    import pylcs # TODO: loosely_contains is not used now. moving the import for pylcs in here, since causing problems for some
    y_words = y.split(" ")
    y_words_contained = []
    for y_word in y_words:
        if lcs_match_y(x, y_word) > 80:
            y_words_contained.append(True)
        else:
            y_words_contained.append(False)

    if match_mode == "any":
        contains = True in y_words_contained
    elif match_mode == "all":
        contains = not(False in y_words_contained)
    else:
        raise Exception("")

    return(contains)


def extract_keyphrases_single_top_aspect_single_review(product_category, top_aspect, overall_sentiment, review):

    if review["top_aspect_sentiments"] is None:
        return(None)

    review_sentiment = review["top_aspect_sentiments"].get(top_aspect, None)
    # TODO: Match the overall_sentiment to the review's sentiment for this aspect
    if overall_sentiment is None or (not overall_sentiment in ["positive", "negative"]) or review_sentiment is None or review_sentiment != overall_sentiment:
        return(None)

    # Run prompt
    prompt_template_filename = "insights_generator/core/prompt_template_keyphrase_extraction_top_aspects.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template = prompt_template_file.read()

    prompt_parameters = {"product_category" : product_category,
            "review_text" : review["review_text"],
            "top_aspect" : top_aspect}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)

    completion = OAI_client.make_prompt_request(prompt, max_tokens = 500, timeout = 2)

    if completion is None:
        return(None)

    keyphrases = []
    completion_lines = completion.split("\n")
    for completion_line in completion_lines:
        if len(completion_line) > 0 and completion_line[0] == "-":
            # The below two lines are a hinderance actually
            #loosely_contained = loosely_contains(completion_line, top_aspect)
            #if loosely_contained:
            keyphrases.append(completion_line[1:])

    if len(keyphrases) == 0:
        return(None)

    keyphrases = {"keyphrases" : keyphrases, "profile_name" : review["profile_name"], "location" : review["location"]}

    return(keyphrases)

def extract_keyphrases_for_top_aspects(product_category, reviews, top_aspects, overall_statistics_dict):

    for top_aspect, statistics in overall_statistics_dict.items():

        overall_sentiment = statistics["overall_sentiment"]
        if overall_sentiment is None:
            overall_statistics_dict[top_aspect]["keyphrases"] = None
            continue

        print("Extracting keyphrases for " + top_aspect)
        n_jobs = 1
        keyphrases = Parallel(n_jobs = n_jobs)(delayed(extract_keyphrases_single_top_aspect_single_review)(product_category, top_aspect, overall_sentiment, review) for review in reviews)
        #review["keyphrases"] = keyphrases # TODO: Fix corner case and add this back in (keyphrases back to review)
        print("Done.")

        keyphrases_for_top_aspect = []
        for keyphrases_for_review in keyphrases:
            if not keyphrases_for_review is None:
                keyphrases_for_top_aspect.append(keyphrases_for_review)

        overall_statistics_dict[top_aspect]["keyphrases"] = keyphrases_for_top_aspect

    return(reviews, overall_statistics_dict)



def extract_aspect_summaries(aspects_dict):

    # For each aspect
    # run the aspect summary prompt to get per aspect summary and action items
    for aspect, aspect_information in aspects_dict.items():

        keyphrases = aspect_information["keyphrases"]
        aspect_summary = None
        aspect_action_items = None

        if not keyphrases is None and len(keyphrases) >= 3:
            # Make prompt and run
            overall_sentiment = aspect_information["overall_sentiment"]

            if overall_sentiment == "positive":

                # Run prompt
                prompt_template_filename = "insights_generator/core/prompt_template_aspect_summary_positive.txt"
                prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
                prompt_template = prompt_template_file.read()

                keyphrases_across_reviews = []
                for keyphrases_per_review in keyphrases:
                    keyphrases_across_reviews.extend(keyphrases_per_review["keyphrases"])

                # Limit to random sample of 10 keyphrases
                if len(keyphrases_across_reviews) > 10:
                    keyphrases_across_reviews = random.sample(keyphrases_across_reviews, 10)
            
                prompt_parameters = {
                        "aspect" : aspect,
                        "keyphrases" : "\n".join(keyphrases_across_reviews)
                        }
            
                prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
            
                completion = OAI_client.make_prompt_request(prompt, max_tokens = 500, timeout = 10)

                aspect_summary = ""
                if not completion is None and len(completion) > 0:
                    # Strip whitespace
                    aspect_summary = completion.strip()
                    aspect_summary = aspect_summary.split("\n")[0]

            elif overall_sentiment == "negative":

                # Run prompt
                prompt_template_filename = "insights_generator/core/prompt_template_aspect_summary_negative.txt"
                prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
                prompt_template = prompt_template_file.read()

                keyphrases_across_reviews = []
                for keyphrases_per_review in keyphrases:
                    keyphrases_across_reviews.extend(keyphrases_per_review["keyphrases"])
            
                # Limit to random sample of 10 keyphrases
                if len(keyphrases_across_reviews) > 10:
                    keyphrases_across_reviews = random.sample(keyphrases_across_reviews, 10)
            
                prompt_parameters = {
                        "aspect" : aspect,
                        "keyphrases" : "\n".join(keyphrases_across_reviews)
                        }
            
                prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
                #print(prompt)
            
                completion = OAI_client.make_prompt_request(prompt, max_tokens = 500, timeout = 10)
                #print(completion)

                aspect_summary = ""
                aspect_action_items = ""
                if not completion is None and len(completion) > 0:
                    # parse completion, by taking everything between 1 and 2 as summary etc
    
                    p = re.compile("1((.|\n)*)2")
                    result = p.search(completion)
                    if not result is None:
                        aspect_summary = result.group(1)
                    aspect_summary = aspect_summary.strip(" .")
                
                    p = re.compile("2((.|\n)*)")
                    result = p.search(completion)
                    if not result is None:
                        aspect_action_items = result.group(1)
                    aspect_action_items = aspect_action_items.strip(" .")

        aspect_information["aspect_summary"] = aspect_summary
        aspect_information["aspect_action_items"] = aspect_action_items

    return(aspects_dict)
