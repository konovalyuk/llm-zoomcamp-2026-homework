import json
import sys
from functools import partial
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from tqdm.auto import tqdm

from shared.load_lessons import load_lessons

# hw2 search utilities
HW2_DIR = Path(__file__).resolve().parent.parent / "hw2"
sys.path.insert(0, str(HW2_DIR))
from search_utils import (  # noqa: E402
    build_chunks,
    build_text_index,
    build_vector_index,
    get_embedder,
    rrf,
)

# hw4 evaluation helpers (course code)
HW4_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HW4_DIR))
from evaluation_utils import llm_structured  # noqa: E402

load_dotenv()

MODEL = "gpt-5.4-mini"
FIRST_PAGES = [
    "01-agentic-rag/lessons/01-intro.md",
    "01-agentic-rag/lessons/02-environment.md",
    "01-agentic-rag/lessons/03-rag.md",
]

DATA_GEN_INSTRUCTIONS = """
You emulate a student who is taking our LLM course.
You are given one lesson page from the course.
Formulate 5 questions this student might ask that are answered by this page.

Rules:
- The page should contain the answer to each question.
- Make the questions complete and not too short.
- Use as few words as possible from the page; don't copy its phrasing.
- The questions should resemble how people actually ask things online:
  not too formal, not too short, not too long.
- Ask about the content of the lesson, not about its formatting or filename.
""".strip()


class Questions(BaseModel):
    questions: list[str]


def compute_relevance(q, search_function):
    filename = q["filename"]
    results = search_function(query=q["question"])
    return [int(d["filename"] == filename) for d in results]


def compute_relevance_total(ground_truth, search_function):
    relevance_total = []
    for q in tqdm(ground_truth, desc="compute_relevance"):
        relevance_total.append(compute_relevance(q, search_function))
    return relevance_total


def hit_rate(relevance):
    cnt = sum(1 for line in relevance if 1 in line)
    return cnt / len(relevance)


def mrr(relevance):
    total_score = 0.0
    for line in relevance:
        for rank, val in enumerate(line):
            if val == 1:
                total_score += 1 / (rank + 1)
                break
    return total_score / len(relevance)


def evaluate(ground_truth, search_function):
    relevance_total = compute_relevance_total(ground_truth, search_function)
    return {
        "hit_rate": hit_rate(relevance_total),
        "mrr": mrr(relevance_total),
    }


def make_text_search(text_index):
    def text_search(query, num_results=5):
        return text_index.search(query, num_results=num_results)

    return text_search


def make_vector_search(vector_index, embedder):
    def vector_search(query, num_results=5):
        query_vector = embedder.encode(query)
        return vector_index.search(query_vector, num_results=num_results)

    return vector_search


def make_hybrid_search(text_index, vector_index, embedder, k=60):
    def hybrid_search(query):
        text_results = text_index.search(query, num_results=10)
        query_vector = embedder.encode(query)
        vector_results = vector_index.search(query_vector, num_results=10)
        return rrf([vector_results, text_results], k=k)

    return hybrid_search


def q1(client, documents):
    pages = [d for d in documents if d["filename"] in FIRST_PAGES]
    usages = []
    for doc in pages:
        user_prompt = json.dumps(
            {"filename": doc["filename"], "content": doc["content"]}
        )
        _, usage = llm_structured(
            client,
            DATA_GEN_INSTRUCTIONS,
            user_prompt,
            Questions,
            model=MODEL,
        )
        usages.append(usage.input_tokens)
    avg_tokens = sum(usages) / len(usages)
    print(f"Q1. avg input tokens (3 pages): {avg_tokens:.1f}")
    print(f"    per page: {usages}")
    return avg_tokens


def q2(ground_truth, text_search_fn):
    q = ground_truth[0]["question"]
    results = text_search_fn(query=q)
    filename = results[0]["filename"]
    print(f"Q2. text search first result: {filename}")
    return filename


def q3(ground_truth, vector_search_fn):
    q = ground_truth[0]["question"]
    results = vector_search_fn(query=q)
    filename = results[0]["filename"]
    print(f"Q3. vector search first result: {filename}")
    return filename


def q4_eval(ground_truth, text_search_fn):
    metrics = evaluate(ground_truth, text_search_fn)
    print(f"Q4. text search hit_rate: {metrics['hit_rate']:.4f}")
    return metrics["hit_rate"]


def q5_eval(ground_truth, vector_search_fn):
    metrics = evaluate(ground_truth, vector_search_fn)
    print(f"Q5. vector search mrr: {metrics['mrr']:.4f}")
    return metrics["mrr"]


def q6_tune(ground_truth, text_index, vector_index, embedder):
    best_k = None
    best_mrr = -1.0
    results = {}
    for k in [1, 50, 100, 200]:
        hybrid_fn = make_hybrid_search(text_index, vector_index, embedder, k=k)
        metrics = evaluate(ground_truth, hybrid_fn)
        results[k] = metrics
        print(f"  k={k}: hit_rate={metrics['hit_rate']:.4f}, mrr={metrics['mrr']:.4f}")
        if metrics["mrr"] > best_mrr:
            best_mrr = metrics["mrr"]
            best_k = k
    print(f"Q6. best k (smallest on tie): {best_k}")
    return best_k, results


def main():
    print("Loading data...")
    documents = load_lessons()
    chunks = build_chunks(documents)
    embedder = get_embedder()
    text_index = build_text_index(chunks)
    vector_index, _ = build_vector_index(chunks, embedder)

    text_search_fn = make_text_search(text_index)
    vector_search_fn = make_vector_search(vector_index, embedder)

    ground_truth = pd.read_csv(HW4_DIR / "ground-truth.csv").to_dict(orient="records")

    print("\n--- Q1 ---")
    try:
        client = OpenAI()
        q1(client, documents)
    except Exception as exc:
        print(f"Q1 skipped (API): {exc}")

    print("\n--- Q2 ---")
    q2(ground_truth, text_search_fn)

    print("\n--- Q3 ---")
    q3(ground_truth, vector_search_fn)

    print("\n--- Q4 ---")
    q4_eval(ground_truth, text_search_fn)

    print("\n--- Q5 ---")
    q5_eval(ground_truth, vector_search_fn)

    print("\n--- Q6 ---")
    q6_tune(ground_truth, text_index, vector_index, embedder)


if __name__ == "__main__":
    main()
