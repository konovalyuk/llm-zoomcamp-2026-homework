# HW4 — Evaluation

Answers for the [submission form](https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw4).

Run:

```bash
cd hw4
uv run python hw4.py
```

Q1 requires valid `OPENAI_API_KEY` in `.env`. Q2–Q6 run offline.

## Q1. Average input tokens (first 3 pages)

Pages: `01-intro.md`, `02-environment.md`, `03-rag.md`

**1400** (~1100–1600 per call; run `hw4.py` with API key to verify)

## Q2. Text search first result

First ground-truth question:

**`01-agentic-rag/lessons/03-rag.md`**

## Q3. Vector search first result

Same question:

**`01-agentic-rag/lessons/01-intro.md`**

(Ground truth is `01-intro.md` — vector finds it; text does not.)

## Q4. Text search Hit Rate

**0.76** (measured: 0.7583)

## Q5. Vector search MRR

**0.55** (measured: 0.5486)

## Q6. Best hybrid RRF k

Tested k = 1, 50, 100, 200:

| k | Hit Rate | MRR |
|---|----------|-----|
| 1 | 0.8361 | 0.6372 |
| 50 | 0.8333 | 0.6379 |
| 100 | 0.8333 | 0.6379 |
| 200 | 0.8333 | 0.6379 |

**50** (best MRR; smallest k on tie)
