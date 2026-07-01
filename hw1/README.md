# HW1 — Agentic RAG

Answers for the [submission form](https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw1).

Run (requires valid `OPENAI_API_KEY` in `.env` for Q3–Q6):

```bash
cd hw1
uv run python hw1.py
```

## Q1. How many lesson pages?

**72**

## Q2. First search result filename

Query: *How does the agentic loop keep calling the model until it stops?*

**`01-agentic-rag/lessons/14-agentic-loop.md`**

## Q3. RAG input tokens (full documents)

Model: `gpt-5.4-mini`

**7000** (~7172 measured; pick closest option)

## Q4. Number of chunks

`chunk_documents(documents, size=2000, step=1000)`

**295**

## Q5. Chunked RAG vs full documents

**3× fewer** input tokens (full-doc ~7172 vs chunked ~2299)

## Q6. Agent search calls

Question: *How does the agentic loop work, and how is it different from plain RAG?*

**4** (varies between runs; re-run `hw1.py` to verify with your API key)
