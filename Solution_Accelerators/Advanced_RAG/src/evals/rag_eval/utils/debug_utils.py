import pandas as pd
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


def get_mock_benchmark_answers(benchmark_questions: pd.DataFrame) -> pd.DataFrame:
    """
    Mock answers from RAG Bot by using an LM to paraphrase the ground-truth answer. Don"t include search context.
    This is useful for testing the evaluation pipeline without having to call RAG Bot which can be slow.

    Args:
        benchmark_questions (pd.DataFrame): The benchmark questions.

    Returns:
        pd.DataFrame: The evaluation set with mocked RAG Bot answers
    """

    tokenizer = AutoTokenizer.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base")
    paraphraser = AutoModelForSeq2SeqLM.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base")
    generate_args = {
        "temperature": 0.9,
        "max_length": 1024,
    }

    answer_records = []
    description = "Generating mock answers using a paraphraser model."
    for index, row in tqdm(benchmark_questions.iterrows(), total=len(benchmark_questions), desc=description):
        answer = row["ground_truth"]
        input_ids = tokenizer(
            f"paraphrase: {answer}",
            return_tensors="pt",
            padding="longest",
            max_length=1024,
            truncation=True,
        )
        outputs = paraphraser.generate(**input_ids, **generate_args)
        paraphrased_answer = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        answer_records.append(
            {
                "Model Answers": paraphrased_answer,
                "Citations": [],
                "Contexts": [],
                "Context Scores": [],
            }
        )

        print(f"\nTrue Answer: {answer}")
        print(f"\nMock Model Answer: {paraphrased_answer}\n")
        print(("=" * 50) + "\n")

    benchmark_answers = pd.concat([benchmark_questions, pd.DataFrame(answer_records)], axis=1)
    return benchmark_answers
