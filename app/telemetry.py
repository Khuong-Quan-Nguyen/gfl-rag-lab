"""Per-request trace rows -> Postgres `traces` table (one row per /ask call)."""
from __future__ import annotations

import logging
import threading
import uuid

import psycopg

from app.config import settings

log = logging.getLogger(__name__)
_lock = threading.Lock()
_conn: psycopg.Connection | None = None

_FIELDS = ("trace_id", "mode", "question", "embed_ms", "retrieve_ms", "rerank_ms", "llm_ms", "total_ms",
           "top_score", "n_chunks", "tokens_in", "tokens_out", "cost_usd", "abstained", "status", "error")


def new_trace_id() -> str:
    return str(uuid.uuid4())


def record(trace: dict) -> None:
    """Insert one trace row. Telemetry must never break a request, so failures are only logged."""
    global _conn
    try:
        with _lock:
            if _conn is None or _conn.closed:
                _conn = psycopg.connect(settings.pg_dsn, autocommit=True)
            cols = ", ".join(_FIELDS)
            ph = ", ".join(["%s"] * len(_FIELDS))
            _conn.execute(f"INSERT INTO traces ({cols}) VALUES ({ph})", [trace.get(f) for f in _FIELDS])
    except Exception:  # noqa: BLE001
        log.exception("failed to record trace")
