"""Homework 5: Monitoring with OpenTelemetry."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

# OTel provider must be ready before importing starter (which builds the RAG).
provider = TracerProvider()
console_processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(console_processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("llm-zoomcamp")

from rag_helper import RAGBase  # noqa: E402
from starter import rag as base_rag  # noqa: E402

QUERY = "How does the agentic loop keep calling the model until it stops?"
DB_PATH = Path(__file__).resolve().parent / "traces.db"


def calc_cost(input_tokens: int, output_tokens: int) -> float:
    input_price_per_million = 0.75
    output_price_per_million = 4.50
    return (input_tokens / 1_000_000) * input_price_per_million + (
        output_tokens / 1_000_000
    ) * output_price_per_million


class RAGTraced(RAGBase):
    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            results = super().search(query, num_results=num_results)
            span.set_attribute("num_results", len(results))
            return results

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)
            usage = response.usage
            span.set_attribute("input_tokens", usage.input_tokens)
            span.set_attribute("output_tokens", usage.output_tokens)
            span.set_attribute(
                "cost", calc_cost(usage.input_tokens, usage.output_tokens)
            )
            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            span.set_attribute("query", query)
            return super().rag(query)


class SQLiteSpanExporter(SpanExporter):
    def __init__(self, db_path="traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spans (
                name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL
            )
            """
        )
        self.conn.commit()

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (
                    span.name,
                    span.start_time,
                    span.end_time,
                    attrs.get("input_tokens"),
                    attrs.get("output_tokens"),
                    attrs.get("cost"),
                ),
            )
        self.conn.commit()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.conn.close()

    def force_flush(self, timeout_millis: int = 30000):
        return True


def span_duration_ms(start_time: int, end_time: int) -> float:
    # OTel times are nanoseconds
    return (end_time - start_time) / 1_000_000


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Swap console exporter for SQLite after a warm-up console run is optional;
    # we use SQLite for all runs and also print answers.
    provider.add_span_processor(SimpleSpanProcessor(SQLiteSpanExporter(str(DB_PATH))))

    rag = RAGTraced(
        index=base_rag.index,
        llm_client=base_rag.llm_client,
        instructions=base_rag.instructions,
        prompt_template=base_rag.prompt_template,
        model=base_rag.model,
    )

    print("=== Running RAG 4 times ===")
    for i in range(4):
        answer = rag.rag(QUERY)
        print(f"\n--- Run {i + 1} ---")
        print(answer[:300], "..." if len(answer) > 300 else "")

    df = pd.read_sql_query("SELECT * FROM spans", sqlite3.connect(DB_PATH))
    df["duration_ms"] = df.apply(
        lambda r: span_duration_ms(r["start_time"], r["end_time"]), axis=1
    )

    # Q1: spans per single trace (rag + search + llm)
    spans_per_run = len(df) // 4
    print("\n=== Answers ===")
    print(f"Q1. Spans per trace: {spans_per_run}")
    print(f"    Closest option: {min([1, 3, 5, 7], key=lambda x: abs(x - spans_per_run))}")

    # Q2: input tokens from first llm span
    llm_spans = df[df["name"] == "llm"].reset_index(drop=True)
    first_input = int(llm_spans.loc[0, "input_tokens"])
    print(f"Q2. Input tokens (first run): {first_input}")
    print(f"    Closest option: {min([700, 7000, 70000, 700000], key=lambda x: abs(x - first_input))}")

    # Q3: typical LLM duration (skip first if cold)
    llm_durations = llm_spans["duration_ms"].tolist()
    typical = sorted(llm_durations)[len(llm_durations) // 2]
    print(f"Q3. LLM durations (ms): {[round(d, 1) for d in llm_durations]}")
    print(f"    Typical (median): {typical:.1f} ms")
    if typical < 100:
        q3 = "Under 100ms"
    elif typical < 500:
        q3 = "100-500ms"
    elif typical < 2000:
        q3 = "500-2000ms"
    else:
        q3 = "Over 2000ms"
    print(f"    Answer: {q3}")

    # Q4: span names
    names = sorted(df["name"].unique().tolist())
    print(f"Q4. Span names: {names}")

    # Q5: total time excluding rag
    children = df[df["name"] != "rag"]
    totals = children.groupby("name")["duration_ms"].sum().sort_values(ascending=False)
    print("Q5. Total duration by span (excl. rag):")
    print(totals.to_string())
    print(f"    Most time: {totals.index[0]}")

    # Q6: input token stability
    inputs = llm_spans["input_tokens"].astype(int).tolist()
    mn, mx = min(inputs), max(inputs)
    spread = (mx - mn) / mn if mn else 0
    print(f"Q6. Input tokens across 4 runs: {inputs}")
    print(f"    Relative spread: {spread:.4%}")
    if mn == mx:
        q6 = "They're identical"
    elif spread <= 0.10:
        q6 = "Within 10% of each other"
    elif spread <= 0.50:
        q6 = "Within 50% of each other"
    else:
        q6 = "They vary more than 50%"
    print(f"    Answer: {q6}")


if __name__ == "__main__":
    main()
