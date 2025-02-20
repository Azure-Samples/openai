# RAG Evaluation

Evaluating Retrieval-Augmented Generation (RAG) systems is crucial to ensure they accurately retrieve relevant information and generate coherent, factually grounded responses, ultimately leading to a better user experience. In the evaluation process, we focus on three key metrics: Accuracy, Groundedness and Relevance, and to evaluate a dataset, we employ Prompt Flow. The evaluation method designed to provide an in-depth assessment of the bot's response generation performance.

**Prompt Flow** works by feeding the bot a series of questions from an [evaluation dataset](./results/MS_RAG_Eval_Dataset.csv) and then comparing the bot's responses to the ideal answers or 'ground truth'. This process enables us to measure the bot's accuracy at different difficulty levels for each question - Easy, Medium, and Hard.

## Heuristics

**Easy**: Questions that can be answered directly from the data in the file without additional calculations.

**Medium**: Questions that require simple calculations or basic analysis to answer. e.g. use of formulae that are not direct hits in the reports. Medium question may also include some table analysis - e.g. *what were top two money making divisions by revenue?*

**Hard**: Questions that require deeper analysis or more complex financial reasoning to answer. Hard questions can be compound questions that can be divided in 2 or more Medium sub-questions.

---

## Evaluation Dataset

The evaluation dataset is a comprehensive set of data that includes the question, ground truth, and the difficulty level for each question.

- **Question**: This represents the query or request made to the bot.
- **Ground Truth**: This is the correct or ideal answer for the question. It acts as the standard against which the bot's response is compared.
- **Difficulty Level**: Each question in the dataset is assigned a difficulty level - Easy, Medium, or Hard.

---

## Evaluation Results

The evaluation results are based on the `top_k` value for Search, with accuracy numbers for each difficulty level in the question.

- **Top_k Value**: This metric represents the number of retrieved documents for the RAG model to consider when generating a response.
- **Accuracy Numbers**: This is the measure of the bot's performance, calculated by comparing the bot's responses to the ground truth. The accuracy numbers are provided for each difficulty level to provide a more detailed insight into the bot's performance.

---

### top_k: 25

Dataset: [MS_RAG_Eval_Dataset_topk_25](./results/MS_RAG_Eval_Dataset_topk_25/benchmark_answers.csv)

| Difficulty Level | Pass Rate |
| ---------------- | --------- |
| Easy             |     87    |
| Medium           |     79    |
| Hard             |     65    |

---

### top_k: 100

Dataset: [MS_RAG_Eval_Dataset_topk_100](./results/MS_RAG_Eval_Dataset_topk_100/benchmark_answers.csv)

| Difficulty Level | Pass Rate |
| ---------------- | --------- |
| Easy             |     94    |
| Medium           |     82    |
| Hard             |     60    |

**Pass Rate: Any answer with at least score 4 is considered correct

---

## Benchmark Datasets

The Benchmark Dataset is a complete set containing the question, generated answer, and full context retrieved from external data sources (vector index).

- **Question**: The query made to the bot.
- **Generated Answer**: The response provided by the bot to the question.
- **Full Context**: All the relevant information or documents that the bot had access to when generating its response.

Each row in the benchmark dataset represents a single instance of a question, the bot's generated answer, and the full context used by the bot. This dataset provides a clear picture of the evaluation data that can be used to assess bot's performance and also for further analysis and improvement of the bot.

---
