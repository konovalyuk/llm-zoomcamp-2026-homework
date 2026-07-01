# HW3 — AI Orchestration with Kestra

Answers for the [submission form](https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw3).

**Important:** Q3–Q5 require running Kestra locally and reading execution logs. Q1–Q2 and Q6 are based on module lessons.

## Local setup

```bash
# 1. Get Gemini API key: https://aistudio.google.com/app/apikey
export GEMINI_API_KEY="your-key"
export SECRET_GEMINI_API_KEY=$(echo -n "$GEMINI_API_KEY" | base64)

# 2. Start Kestra
cd hw3/kestra
docker compose up -d
# UI: http://localhost:8080

# 3. Import flows from course repo
PREFIX=https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/03-orchestration/flows
for f in 1_chat_without_rag.yaml 2_chat_with_rag.yaml 4_simple_agent.yaml; do
  curl -sL "$PREFIX/$f" -o "$f"
  curl -X POST -u 'admin@kestra.io:Admin1234!' \
    http://localhost:8080/api/v1/flows/import -F "fileUpload=@$f"
done

# 4. Stop when done
docker compose down
```

Flows to run in Kestra UI:
- Q2: `1_chat_without_rag.yaml` and `2_chat_with_rag.yaml`
- Q3–Q5: `4_simple_agent.yaml` (check `log_token_usage` task logs)

## Q1. Context Engineering

**AI Copilot has access to current Kestra plugin documentation**

ChatGPT guesses from training data; Kestra AI Copilot is grounded in current plugin docs and valid property names.

## Q2. RAG vs No RAG

**Vague, generic, or fabricated — the model guesses from training data**

Without RAG, the model hallucinates or gives generic answers about Kestra 1.1 features.

## Q3. Token usage — short summary

Run `4_simple_agent.yaml` with `summary_length = short`.

Check `log_token_usage` → `multilingual_agent` output tokens:

**60-100 tokens**

> Verify in your Kestra execution logs after running the flow.

## Q4. Token usage — long summary

Run `4_simple_agent.yaml` with `summary_length = long`.

Compare `multilingual_agent` output tokens to Q3:

**2-5x more**

## Q5. Modifying a flow

In `4_simple_agent.yaml`, change `english_brevity` prompt from **1 sentence** to **3 sentences**.
Run with `summary_length = long`.

Compare `english_brevity` output tokens to the original 1-sentence version:

**2-4x more**

## Q6. Best Practices

**Use traditional task-based workflows for predictability and auditability**

For regulated / compliance workflows, deterministic traditional workflows beat flexible AI agents.

## Repository link for form

https://github.com/konovalyuk/llm-zoomcamp-2026-homework
