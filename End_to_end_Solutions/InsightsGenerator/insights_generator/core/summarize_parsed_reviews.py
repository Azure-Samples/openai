import numpy as np
from collections import defaultdict
from . import OAI_client
from sklearn.cluster import AgglomerativeClustering
from joblib import Parallel, delayed
import itertools
import json


def semantic_clustering(texts, distance_threshold):

    # Currently not used in IG notebooks. But used in other use cases.

    # 1) Calculate embeddings
    print("Calculating embeddings...")
    n_jobs = 5
    print("Starting " + str(n_jobs) + " parallel jobs.")
    embeddings = Parallel(n_jobs = n_jobs)(delayed(OAI_client.calc_embedding)(text) for text in texts)
    print("done.")

    # 2) Make into matrix of num_obs x embedding_dim
    embeddings = np.array(embeddings)
    #print(embeddings.shape)

    # 3) Do hierarchical clustering
    hclust_model = AgglomerativeClustering(n_clusters = None, linkage = "average",
                                           metric = "cosine", distance_threshold = distance_threshold)
    clustering = hclust_model.fit(embeddings)

    # 4) Do some diagnostics
    if True:
        clusters = defaultdict(list)
        for text, cluster_label in zip(texts, clustering.labels_):
            clusters[int(cluster_label)].append(text)
        print("Num clusters: " + str(len(clusters.keys())))
        print("Printing top clusters")
        for cluster_id, cluster_texts in clusters.items():
            if len(cluster_texts) > 5:
                print("Cluster id: " + str(cluster_id))
                print("Size: " + str(len(cluster_texts)))
                print(json.dumps(cluster_texts, indent = 4))
                print()

    return(clustering.labels_)

def get_topic_comments_single_review(review, topic, prompt_template):
    
    prompt_parameters = {
            "review_text" : review["review_text"],
            "topic" : topic
            }
    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
    #print(prompt)
    completion = OAI_client.make_prompt_request(prompt)
    if completion is None:
        comments = []
        return(comments)
    comment_numbers = [x.strip() for x in completion.split(",")]
    parsed_review_text = review["parsed_review_text"]
    #print(comment_numbers)
    #print(parsed_review_text)
    comments = []
    for x in comment_numbers:
        if x in parsed_review_text:
            comments.append((x, parsed_review_text[x]))            
    
    return(comments)


def get_topic_comments(parsed_reviews, topic):
    """Given parsed version of the text corpus, get all lines that are relevant to topic.
    
    Given a text + topic, we ask GPT to generate line numbers for lines relevant to the topic.
    By working with line numbers instead of the lines, we avoid hallucinations in retrived lines.
    We pull relevant lines from all individual texts across the entire corpus.
     
    :param parsed_reviews: The text corpus as a list. Each entry in the list is a dict.
        Each dict must have the key 'review_text', which stores the individual text
        Each dict must have the key 'parsed_review_text', which stores the parsed individual text.
    :param topic: the topic of interest
    :type reviews: list
    :type topic: str
    :returns: list of relevant lines. Each entry is of form (line_number, line_text)
    :rtype: list
    """
    
    
    prompt_template_1 = """{review_text}

The above is a numbered list of comments about minecraft.
Based on the above comments answer the below question.


What comments have suggestions to improve {topic}.
List their comment numbers as a comma seperated list.

Comment numbers:
"""

    print("Getting comments from single reviews...")
    n_jobs = 4
    print("Starting " + str(n_jobs) + " parallel jobs.")
    suggestions = Parallel(n_jobs = n_jobs)(delayed(get_topic_comments_single_review)(review, topic, prompt_template_1) for review in parsed_reviews)
    #print(suggestions)
    #suggestions are of form (number, quoted_comment)
    suggestions = list(itertools.chain(*suggestions))
    print("Done.")
    
    return(suggestions)


# TODO: Move into package
def summarize_cluster(topic, comments):
    """Given a topic and lines that are relevant to the topic, summarize the lines
    
    :param topic: the topic of interest
    :param comments: list of relevant lines. Each entry is of form (line_number, line_text)
    :type topic: string
    :type comments: list
    :returns: summary of lines
    :rtype: string
    """
    
    prompt_template = """{comments_text}

The above is a list of comments about {topic} in a minecraft chat.
Based on the above comments answer the below question.


Summarize the comments.
Summarize top 3 suggestions to improve {topic}. If there are no suggestions, mention 'no suggestions'.

"""
    
    comments_text = ""
    for comment_number, comment_text in comments:
        comments_text += "\n" + comment_text
        
    prompt_parameters = {
            "comments_text" : comments_text,
            "topic" : topic
            }
    prompt = OAI_client.construct_prompt(prompt_parameters, prompt_template)
    #print(prompt)
    completion = OAI_client.make_prompt_request(prompt, timeout = 5)
    
    return(completion)

def get_topic_summaries_with_references(topic, comments, top_cluster_size_threshold):
    """
    Given a topic and lines that are relevant to the topic, extract dominant clusters of lines and summarize each cluster.
    
    comments contains the text of lines that are relevant to topic.
    Use semantic clustering on these lines to get clusters that are:
    1. Semantically highly similar
    2. Have a significant size (number of lines in the cluster > top_cluster_size_threshold)
    Clusters that satisfy these two properties are called dominant clusters, and capture
    the major information in the lines.
    The lines that dont belong to a dominant cluster are discarded before summary.
    Next, we summarize each dominant cluster and include the lines of that cluster as references for that summary.
    Since the dominant cluster is quite homogenous, we will get a good summary.
    Since the lines were extracted from the corpus via line numbers, they are reproduced verbatim here
    and avoid hallucinations in the references.
    Hence we good focussed summary of the dominant points with verbatim / non-hallucinated references.
    
    :param topic: the topic of interest
    :param comments: list of relevant lines. Each entry is of form (line_number, line_text)
    :param top_cluster_size_threshold: minimum size for a cluster to be a dominant cluster
    :type topic: string
    :type comments: list
    :type top_cluster_size_threshold: int
    :returns: Dict of summaries. Keys are the cluster ids, values are the summaries of that cluster.
        The cluster summaries are dicts. Keys are comments, summary.
        The value of comments are the lines in that cluster.
        And summary is the summary of those lines (clusterwise summary).
    :rtype: dict
    """
    
    # 1) Calculate embeddings
    print("Calculating embeddings...")
    n_jobs = 4
    print("Starting " + str(n_jobs) + " parallel jobs.")
    embeddings = Parallel(n_jobs = n_jobs)(delayed(OAI_client.calc_embedding)(comment_text) for comment_number, comment_text in comments)
    print("done.")

    # 2) Make into matrix of num_obs x embedding_dim
    embeddings = np.array(embeddings)
    #print(embeddings.shape)

    # 3) Do hierarchical clustering
    distance_threshold = 0.2
    hclust_model = AgglomerativeClustering(n_clusters = None, linkage = "average",
                                           metric = "cosine", distance_threshold = distance_threshold)
    clustering = hclust_model.fit(embeddings)

    # 4) Massage into clusters of comments
    clusters = defaultdict(list)
    for x, cluster_label in zip(comments, clustering.labels_):
        comment_number, comment_text = x
        clusters[int(cluster_label)].append((comment_number, comment_text))
    print("Num clusters: " + str(len(clusters.keys())))

    # 5) Select the top clusters and summarize them.
    top_clusters = {}
    for cluster_label, comments in clusters.items():
        num_comments_in_cluster = len(comments)
        if num_comments_in_cluster > top_cluster_size_threshold:
            top_cluster_comments = comments
            top_cluster_summary = summarize_cluster(topic, comments)
            top_cluster_info = {"comments" : top_cluster_comments,
                               "summary" : top_cluster_summary}
            top_clusters[cluster_label] = top_cluster_info
    print("Num top clusters: " + str(len(top_clusters.keys())))
            
    return(top_clusters)

def print_topic_summaries_with_references(topic, topic_summaries_with_references):
    """Pretty print the summaries with references of the topic.
    
    :param topic: the topic
    :param topic_summaries_with_references: Dict of summaries. Keys are the cluster ids, values are the summaries of that cluster.
        The cluster summaries are dicts. Keys are comments, summary.
        The value of comments are the lines in that cluster.
        And summary is the summary of those lines (clusterwise summary).
    :type topic: str
    :type topic_summaries_with_references: dict
    """

    print("Topic is: " + topic)
    for cluster_label, summary_with_references in topic_summaries_with_references.items():
        comments = summary_with_references["comments"]
        summary = summary_with_references["summary"]
        print("\nSummary with references:\n")
        print("Summary: \n" + summary + "\n")
        print("References: \n")
        for comment_number, comment_text in comments:
            print(comment_number + ":" + comment_text)
