# HW5 — Monitoring (OpenTelemetry)

Answers for the [submission form](https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw5).

Instructions: [homework.md](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/cohorts/2026/05-monitoring/homework.md)

Run (requires valid `OPENAI_API_KEY` in project `.env`):

```bash
cd hw5
uv run python hw5.py
```

## Q1. How many spans does the trace produce?

**3** (`rag`, `search`, `llm`)

## Q2. How many input tokens for the LLM call?

**7000** (same RAG + query as HW1 ≈7172; pick closest)

## Q3. Roughly how long does the LLM call take?

**Over 2000ms** (typical for ~7k-token context; cold start can be slower)

## Q4. Which span names appear in the spans table?

**rag, search, and llm**

## Q5. Excluding rag, which span type takes the most total time?

**llm** (`search` is ~1–2 ms; LLM dominates)

## Q6. How much do input tokens vary across 4 runs?

**They're identical** (minsearch is deterministic → same retrieved docs → same prompt)
