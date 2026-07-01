# LLM Zoomcamp 2026 — Homework

Personal repository for [LLM Zoomcamp 2026](https://courses.datatalks.club/llm-zoomcamp-2026/) homework submissions.

Course repo: [DataTalksClub/llm-zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp)

## Requirements

- Python 3.10+ (tested with 3.10.12)
- [uv](https://docs.astral.sh/uv/)

> **Note:** `onnxruntime` 1.24+ dropped Python 3.10 support. This project pins `onnxruntime>=1.23,<1.24`.

## Setup

```bash
cd llm-zoomcamp-2026-homework
uv sync
cp .env.example .env   # add your OPENAI_API_KEY
```

## PyCharm interpreter

**Settings → Project → Python Interpreter → Add → Existing:**

```
/home/maksym/my/python/llm-zoomcamp-2026-homework/.venv/bin/python
```

## Structure

| Folder | Module | Status |
|--------|--------|--------|
| `hw1/` | Agentic RAG | done |
| `hw2/` | Vector Search | done |
| `hw3/` | Orchestration (Kestra) | done (Q3–Q5 need local Kestra run) |
| `hw4/` | Evaluation | done (Q1 needs API key) |
| `hw5/` | Monitoring | waiting for assignment |

Shared code for loading course lessons (commit `8c1834d`, 72 pages):

- `shared/load_lessons.py`
- `shared/chunks.py` — `chunk_documents(size=2000, step=1000)`

## Run

```bash
uv run python hw1/hw1.py
uv run python hw2/hw2.py
uv run python hw4/hw4.py
```

Homework form answers go in `hw*/README.md`.
