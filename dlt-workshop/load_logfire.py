"""Load Logfire agent traces into DuckDB with dlt.

Requires LOGFIRE_READ_TOKEN in .env (or .dlt/secrets.toml).
Schema/dataset name: agent_traces (as required by the homework).
"""

from __future__ import annotations

import os
from pathlib import Path

import dlt
from dotenv import load_dotenv
from dlt.sources.helpers.rest_client.paginators import SinglePagePaginator
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

# Project root .env (shared with other homeworks)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv()

# Prefer EU; US works if your project is there — override with LOGFIRE_BASE_URL.
BASE_URL = os.getenv("LOGFIRE_BASE_URL", "https://logfire-api.pydantic.dev/")

SQL = """
SELECT
  trace_id,
  span_id,
  parent_span_id,
  span_name,
  message,
  start_timestamp,
  end_timestamp,
  duration,
  is_exception,
  exception_type,
  exception_message,
  attributes
FROM records
ORDER BY start_timestamp DESC
LIMIT 5000
"""


@dlt.source(name="logfire")
def logfire_source(read_token: str = dlt.secrets.value):
    config: RESTAPIConfig = {
        "client": {
            "base_url": BASE_URL,
            "auth": {
                "type": "bearer",
                "token": read_token,
            },
            "paginator": SinglePagePaginator(),
        },
        "resource_defaults": {
            "write_disposition": "replace",
        },
        "resources": [
            {
                "name": "records",
                "endpoint": {
                    "path": "v1/query",
                    "method": "GET",
                    "params": {"sql": SQL},
                    "data_selector": "columns",
                },
            },
        ],
    }
    yield from rest_api_resources(config)


@dlt.resource(name="records", write_disposition="replace")
def logfire_records(read_token: str):
    """Fetch Logfire query results and yield row dicts (handles column-oriented JSON)."""
    import requests

    resp = requests.get(
        f"{BASE_URL.rstrip('/')}/v1/query",
        params={"sql": SQL},
        headers={"Authorization": f"Bearer {read_token}"},
        timeout=120,
    )
    resp.raise_for_status()
    payload = resp.json()

    # Logfire may return row-oriented or column-oriented JSON.
    if isinstance(payload, list):
        yield from payload
        return

    if "rows" in payload:
        yield from payload["rows"]
        return

    columns = payload.get("columns") or payload.get("data")
    if isinstance(columns, dict):
        keys = list(columns.keys())
        length = len(next(iter(columns.values()))) if keys else 0
        for i in range(length):
            yield {k: columns[k][i] for k in keys}
        return

    if isinstance(columns, list) and columns and isinstance(columns[0], dict):
        # [{name, values}, ...]
        names = [c["name"] for c in columns]
        length = len(columns[0].get("values", []))
        for i in range(length):
            yield {c["name"]: c["values"][i] for c in columns}
        return

    raise ValueError(f"Unexpected Logfire response keys: {list(payload.keys())}")


def load() -> None:
    read_token = os.environ.get("LOGFIRE_READ_TOKEN") or dlt.secrets.get(
        "sources.logfire.read_token"
    )
    if not read_token:
        raise SystemExit(
            "Set LOGFIRE_READ_TOKEN in .env (Logfire project → Settings → Read tokens)"
        )

    pipeline = dlt.pipeline(
        pipeline_name="agent_traces",
        destination="duckdb",
        dataset_name="agent_traces",
    )
    info = pipeline.run(logfire_records(read_token))
    print(info)
    print(pipeline.last_trace.last_normalize_info)

    with pipeline.sql_client() as client:
        rows = client.execute_sql(
            """
            SELECT COUNT(*) AS n
            FROM information_schema.tables
            WHERE table_schema = 'agent_traces'
            """
        )
        print("Q2. Tables in agent_traces schema:", rows[0][0])


if __name__ == "__main__":
    load()
