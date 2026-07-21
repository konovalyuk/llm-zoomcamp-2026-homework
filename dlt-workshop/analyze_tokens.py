"""Q3: sum gen_ai.usage.input_tokens for the Ollama query agent run."""

from __future__ import annotations

import json
from pathlib import Path

import dlt
import duckdb


def extract_input_tokens(attributes) -> int | None:
    if attributes is None:
        return None
    if isinstance(attributes, str):
        try:
            attributes = json.loads(attributes)
        except json.JSONDecodeError:
            return None
    if not isinstance(attributes, dict):
        return None

    for key in (
        "gen_ai.usage.input_tokens",
        "gen_ai.usage.input_tokens".replace(".", "_"),
    ):
        if key in attributes and attributes[key] is not None:
            return int(attributes[key])

    # Nested / flattened variants after dlt normalize
    usage = attributes.get("gen_ai.usage") or attributes.get("gen_ai") or {}
    if isinstance(usage, dict) and usage.get("input_tokens") is not None:
        return int(usage["input_tokens"])
    return None


def main() -> None:
    # Prefer duckdb file created by the pipeline
    db_candidates = [
        Path("agent_traces.duckdb"),
        Path(__file__).resolve().parent / "agent_traces.duckdb",
    ]
    db_path = next((p for p in db_candidates if p.exists()), None)

    if db_path is None:
        pipeline = dlt.attach("agent_traces")
        dataset = pipeline.dataset()
        tables = dataset.row_counts().df()
        print("Tables / row counts:")
        print(tables)

        # Find records table and any attribute child tables
        df = dataset.records.df()
    else:
        con = duckdb.connect(str(db_path))
        n_tables = con.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'agent_traces'
            """
        ).fetchone()[0]
        print("Q2. Tables in agent_traces:", n_tables)
        print(
            con.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'agent_traces'
                ORDER BY table_name
                """
            ).fetchdf()
        )
        df = con.execute("SELECT * FROM agent_traces.records").fetchdf()

    # Prefer traces that mention Ollama in message / attributes
    text_cols = [c for c in df.columns if c in ("message", "span_name")]
    mask = False
    for c in text_cols:
        mask = mask | df[c].astype(str).str.contains("Ollama|ollama", case=False, na=False)

    # Also search attributes JSON
    if "attributes" in df.columns:
        mask = mask | df["attributes"].astype(str).str.contains(
            "Ollama|ollama", case=False, na=False
        )

    subset = df[mask] if mask is not False and mask.any() else df
    trace_ids = subset["trace_id"].dropna().unique().tolist()
    print(f"Candidate traces: {len(trace_ids)}")

    best = None
    for tid in trace_ids:
        spans = df[df["trace_id"] == tid]
        tokens = []
        for _, row in spans.iterrows():
            t = extract_input_tokens(row.get("attributes"))
            if t is not None:
                tokens.append(t)
        # Also check flattened columns from dlt
        for col in spans.columns:
            if "input_tokens" in col.lower():
                vals = spans[col].dropna().tolist()
                tokens.extend(int(v) for v in vals)

        total = sum(tokens)
        n_spans = len(spans)
        print(f"trace={tid[:16]}... spans={n_spans} input_tokens_sum={total} parts={tokens}")
        if best is None or (total > 0 and n_spans >= best[1]):
            best = (tid, n_spans, total, tokens)

    if best:
        tid, n_spans, total, tokens = best
        print("\n=== Best matching run ===")
        print(f"Q1. Spans in run: {n_spans} (closest of 1/5/15/30)")
        print(f"Q3. Total input tokens: {total}")
        if 100 <= total <= 500:
            rng = "100 - 500"
        elif 1500 <= total <= 5000:
            rng = "1500 - 5000"
        elif 10000 <= total <= 20000:
            rng = "10000 - 20000"
        elif 50000 <= total <= 100000:
            rng = "50000 - 100000"
        else:
            rng = f"(outside listed ranges: {total})"
        print(f"Q3. Range: {rng}")


if __name__ == "__main__":
    main()
