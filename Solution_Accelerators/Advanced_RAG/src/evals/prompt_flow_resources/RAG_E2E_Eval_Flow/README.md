# Q&A Evaluation: Similarity

The Q&A Similarity evaluation flow will evaluate the Q&A Retrieval Augmented Generation systems by leveraging the state-of-the-art Large Language Models (LLM) to measure the quality and safety of your responses. Utilizing GPT as the Language Model to assist with measurements aims to achieve a high agreement with human evaluations compared to traditional mathematical measurements.

## What you will learn

The Similarity evaluation flow allows you to assess and evaluate your model with the LLM-assisted Similarity metric.

**gpt_similarity**: Measures similarity between user-provided ground truth answers and the model predicted answer.

Similarity is scored on a scale of 1 to 5, with 1 being the worst and 5 being the best.

## Prerequisites

- Connection: Azure OpenAI or OpenAI connection.
- Data input: Evaluating the Similarity metric requires you to provide data inputs including a question, a ground truth, and an answer. 

## Tools used in this flow
- LLM tool
- Python tool