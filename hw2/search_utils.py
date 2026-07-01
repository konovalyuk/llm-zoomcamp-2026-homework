import sys
from pathlib import Path

import numpy as np
from minsearch import Index, VectorSearch

from shared.chunks import chunk_lessons
from shared.load_lessons import load_lessons

EMBED_DIR = Path(__file__).resolve().parent / "embed"
sys.path.insert(0, str(EMBED_DIR))

from embedder import Embedder  # noqa: E402

MODEL_PATH = EMBED_DIR / "models" / "Xenova" / "all-MiniLM-L6-v2"
QUERY_Q1 = "How does approximate nearest neighbor search work?"


def get_embedder():
    return Embedder(path=str(MODEL_PATH))


def build_chunks(documents=None):
    if documents is None:
        documents = load_lessons()
    return chunk_lessons(documents)


def build_text_index(chunks):
    index = Index(
        text_fields=["content"],
        keyword_fields=["filename"],
    )
    index.fit(chunks)
    return index


def build_vector_index(chunks, embedder=None):
    if embedder is None:
        embedder = get_embedder()
    vectors = embedder.encode_batch([c["content"] for c in chunks])
    index = VectorSearch(keyword_fields=["filename"])
    index.fit(vectors, chunks)
    return index, embedder


def text_search(query, num_results=5, text_index=None):
    if text_index is None:
        raise ValueError("text_index is required")
    return text_index.search(query, num_results=num_results)


def vector_search(query, num_results=5, vector_index=None, embedder=None):
    if vector_index is None or embedder is None:
        raise ValueError("vector_index and embedder are required")
    query_vector = embedder.encode(query)
    return vector_index.search(query_vector, num_results=num_results)


def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc

    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]


def hybrid_search(query, k=60, num_results=5, text_index=None, vector_index=None, embedder=None):
    text_results = text_search(query, num_results=10, text_index=text_index)
    vector_results = vector_search(
        query, num_results=10, vector_index=vector_index, embedder=embedder
    )
    return rrf([vector_results, text_results], k=k, num_results=num_results)
