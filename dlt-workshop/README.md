# dlt Workshop

Answers for the [submission form](https://courses.datatalks.club/llm-zoomcamp-2026/homework/dlt).

Instructions: [homework.md](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/cohorts/2026/workshops/dlt/homework.md)

## Setup

1. Put keys in the project root `.env`:

```
OPENAI_API_KEY=sk-...
LOGFIRE_TOKEN=...          # write token (Logfire → project → Write tokens)
LOGFIRE_READ_TOKEN=...     # read token (Settings → Read tokens)
```

2. Create a free [Logfire](https://logfire.dev) project and generate write + read tokens.

3. Run the instrumented agent (creates traces in Logfire):

```bash
cd dlt-workshop
uv run python main.py
```

4. Load traces into DuckDB and count tables:

```bash
uv run python load_logfire.py
```

5. Analyze spans / tokens for the Ollama query:

```bash
uv run python analyze_tokens.py
```

## Questions (fill after running)

### Q1. Spans for "How do I run Ollama locally?"

**_pending_** (expected ~**5** — agent + LLM calls + tool searches; varies)

### Q2. Tables in `agent_traces` schema

**_pending_** (dlt normalizes nested JSON → often around **24**)

### Q3. Total input tokens for that agent run

**_pending_** (sum of `gen_ai.usage.input_tokens`; expected **1500 - 5000**)
