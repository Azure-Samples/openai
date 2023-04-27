from . import OAI_client
import re
from . import extract_statistical_summary
import random
import pdb

MIN_SENTIMENT_PERCENTAGE = 75

def extract_direct_answer(reviews, user_query:str):
    print ("Reached summary from {len(reviews)} reviews")
    print (reviews[0])
    prompt_template_filename = "insights_generator/core/prompt_template_direct_summary.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template_summary = prompt_template_file.read()
    
    review_texts = []
    for i, review in enumerate(reviews):
        review_text = review["review_text"]
        if len(review_text) > 0:
            review_texts.append(review_text)
            #stars = review["stars"]
            #sentiment_aspects = sentiment_aspects + [f"## Review {i + 1} - {stars}"] + review["sentiment_aspects_NL"]

    prompt_parameters = {"review_texts" : "\n".join(review_texts), "question": user_query}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template_summary)
    print (f"Interactive prompt: {prompt}")
    timeout = 10
    max_tokens = 200
    completion = OAI_client.make_prompt_request(prompt, max_tokens = max_tokens, timeout = timeout)
    out_summary = {"answer" : completion}

    return out_summary

def overall_statistics_to_raw_text(overall_statistics_dict):

    # Get the positive and negative aspects separately
    positive_aspects = []
    negative_aspects = []
    for top_aspect, statistics in overall_statistics_dict.items():
        percentage_positive = statistics["percentage_positive"]
        if not percentage_positive is None:
            percentage_negative = 100 - percentage_positive
            if percentage_positive >= MIN_SENTIMENT_PERCENTAGE:
                positive_aspects.append(top_aspect)
            elif percentage_negative >= MIN_SENTIMENT_PERCENTAGE:
                negative_aspects.append(top_aspect)

    # Convert into raw text
    raw_text = ""
    for positive_aspect in positive_aspects:
        raw_text += "{} is good.\n".format(positive_aspect)

    for negative_aspect in negative_aspects:
        raw_text += "{} is bad.\n".format(negative_aspect)

    return(raw_text)

def extract_statistical_summary_NL(product_category, overall_statistics_dict):

    statistics_raw_text = overall_statistics_to_raw_text(overall_statistics_dict)
    prompt_template_filename = "insights_generator/core/prompt_template_statistics_raw_text_to_NL.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template_summary = prompt_template_file.read()
    
    prompt_parameters = {"product_category" : product_category, "comments" : statistics_raw_text}

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template_summary)

    timeout = 10
    max_tokens = 200
    completion = OAI_client.make_prompt_request(prompt, max_tokens = max_tokens, timeout = timeout)
    overall_summary = completion.strip()

    print("Extracted NL version of statistical summary.")

    summary = {"overall" : overall_summary}

    return(summary)


def summarize_aspect_summaries(product_category, aspect_summaries):

    if len(aspect_summaries) == 0:
        return("")

    prompt_template_filename = "insights_generator/core/prompt_template_summarize_aspect_summaries.txt"
    prompt_template_file = open(prompt_template_filename, encoding = "utf-8")
    prompt_template = prompt_template_file.read()

    # Limit to random sample of 10 aspects
    MAX_ASPECTS_COUNT = 10
    if len(aspect_summaries) > MAX_ASPECTS_COUNT:
        aspect_summaries = random.sample(aspect_summaries, MAX_ASPECTS_COUNT)

    prompt_parameters = {
            "product_category" : product_category,
            "aspect_summaries" : "\n".join(aspect_summaries)
            }

    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)

    timeout = 10
    max_tokens = 500
    completion = OAI_client.make_prompt_request(prompt, max_tokens = max_tokens, timeout = timeout)

    # Strip whitespace
    completion = completion.strip()

    return(completion)

def extract_highlights_lowlights(product_category, aspects_dict):

    # Get the positive aspect summaries
    # and the negative aspect summaries
    positive_aspect_summaries = []
    negative_aspect_summaries = []
    for aspect, aspect_information in aspects_dict.items():

        aspect_summary = aspect_information["aspect_summary"]

        if not aspect_summary is None:
            overall_sentiment = aspect_information["overall_sentiment"]

            if overall_sentiment == "positive":
                positive_aspect_summaries.append(aspect_summary)
            elif overall_sentiment == "negative":
                negative_aspect_summaries.append(aspect_summary)

    # Get the highlights
    highlights = summarize_aspect_summaries(product_category, positive_aspect_summaries)
    lowlights = summarize_aspect_summaries(product_category, negative_aspect_summaries)

    
    summary = {"highlights" : highlights, "lowlights" : lowlights}

    return(summary)


def extract_summary(product_category, aspects_dict):

    summary = {}

    # Get the overall
    overall_summary = extract_statistical_summary_NL(product_category, aspects_dict)
    summary.update(overall_summary)

    # Get the high and low lights
    high_low_lights_summary = extract_highlights_lowlights(product_category, aspects_dict)
    summary.update(high_low_lights_summary)

    # Get the action items
    action_items = {}
    for aspect, aspect_information in aspects_dict.items():
        aspect_action_items = aspect_information["aspect_action_items"]
        if not aspect_action_items is None:
            action_items[aspect] = aspect_action_items

    summary["action_items"] = action_items

    return(summary)
