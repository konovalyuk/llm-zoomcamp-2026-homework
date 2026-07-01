import sys
from pathlib import Path

import numpy as np

from shared.load_lessons import load_lessons

from search_utils import (
    QUERY_Q1,
    build_chunks,
    build_text_index,
    build_vector_index,
    get_embedder,
    hybrid_search,
    rrf,
    text_search,
    vector_search,
)

EMBED_DIR = Path(__file__).resolve().parent / "embed"
sys.path.insert(0, str(EMBED_DIR))


def q1(embedder):
    v = embedder.encode(QUERY_Q1)
    print(f"Q1. v[0] = {v[0]:.4f}")
    return v


def q2(documents, embedder, v):
    target = "02-vector-search/lessons/07-sqlitesearch-vector.md"
    doc = next(d for d in documents if d["filename"] == target)
    doc_v = embedder.encode(doc["content"])
    similarity = float(np.dot(v, doc_v))
    print(f"Q2. cosine similarity = {similarity:.4f}")
    return similarity


def q3(chunks, embedder, v):
    X = embedder.encode_batch([c["content"] for c in chunks])
    scores = X.dot(v)
    best_idx = int(np.argmax(scores))
    filename = chunks[best_idx]["filename"]
    print(f"Q3. top chunk filename = {filename}")
    return filename


def q4(vector_index, embedder):
    query = "What metric do we use to evaluate a search engine?"
    results = vector_search(query, vector_index=vector_index, embedder=embedder)
    filename = results[0]["filename"]
    print(f"Q4. first result = {filename}")
    return filename


def q5(text_index, vector_index, embedder):
    query = "How do I store vectors in PostgreSQL?"
    text_results = text_search(query, num_results=5, text_index=text_index)
    vector_results = vector_search(
        query, num_results=5, vector_index=vector_index, embedder=embedder
    )
    text_files = {r["filename"] for r in text_results}
    vector_only = [
        r["filename"] for r in vector_results if r["filename"] not in text_files
    ]
    print(f"Q5. vector but not text: {vector_only}")
    return vector_only[0] if vector_only else None


def q6(text_index, vector_index, embedder):
    query = "How do I give the model access to tools?"
    text_results = text_search(query, num_results=10, text_index=text_index)
    vector_results = vector_search(
        query, num_results=10, vector_index=vector_index, embedder=embedder
    )
    results = rrf([vector_results, text_results])
    filename = results[0]["filename"]
    print(f"Q6. RRF first result = {filename}")
    return filename


def main():
    print("Loading data and building indexes...")
    documents = load_lessons()
    chunks = build_chunks(documents)
    embedder = get_embedder()
    text_index = build_text_index(chunks)
    vector_index, _ = build_vector_index(chunks, embedder)

    print("\n--- Q1 ---")
    v = q1(embedder)

    print("\n--- Q2 ---")
    sim = q2(documents, embedder, v)

    print("\n--- Q3 ---")
    q3_file = q3(chunks, embedder, v)

    print("\n--- Q4 ---")
    q4_file = q4(vector_index, embedder)

    print("\n--- Q5 ---")
    q5_file = q5(text_index, vector_index, embedder)

    print("\n--- Q6 ---")
    q6_file = q6(text_index, vector_index, embedder)

    print("\n=== Form answers ===")
    q1_opts = [-0.31, -0.02, 0.12, 0.44]
    q1_ans = min(q1_opts, key=lambda x: abs(x - v[0]))
    q2_opts = [0.07, 0.37, 0.68, 0.92]
    q2_ans = min(q2_opts, key=lambda x: abs(x - sim))
    print(f"Q1: {q1_ans}")
    print(f"Q2: {q2_ans}")
    print(f"Q3: {q3_file}")
    print(f"Q4: {q4_file}")
    print(f"Q5: {q5_file}")
    print(f"Q6: {q6_file}")


if __name__ == "__main__":
    main()
