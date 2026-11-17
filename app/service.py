"""FastAPI service. The embedder and cross-encoder load ONCE at startup (the long-lived-service fix).

Run:  uvicorn app.service:app --port 8000
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import telemetry
from app.config import settings
from app.generate import answer
from app.retrieval import MODELS, search

Mode = Literal["vector", "hybrid", "vector_rerank", "hybrid_rerank"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    t0 = time.perf_counter()
    MODELS.load(rerank=True)
    search("warm up", "hybrid_rerank", k=1)  # first call pays one-off kernel/DB setup
    app.state.startup_s = time.perf_counter() - t0
    yield


app = FastAPI(title="gfl-rag-lab", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    mode: Mode = "hybrid_rerank"
    k: int = Field(10, ge=1, le=50)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "models_loaded": MODELS.reranker is not None,
            "startup_s": round(getattr(app.state, "startup_s", 0.0), 2),
            "llm_enabled": bool(settings.anthropic_api_key), "abstain_threshold": settings.abstain_threshold}


@app.post("/search")
def search_only(req: AskRequest) -> dict:
    """Retrieval only (no LLM, no trace) - used by the latency demo and evals."""
    return search(req.question, req.mode, req.k).to_dict()


@app.post("/ask")
def ask(req: AskRequest) -> dict:
    """Retrieve, apply the abstain guardrail, answer with citations, and record one trace row."""
    trace_id = telemetry.new_trace_id()
    t0 = time.perf_counter()
    trace = {"trace_id": trace_id, "mode": req.mode, "question": req.question}
    try:
        res = search(req.question, req.mode, req.k)
        ans = answer(req.question, res.hits, res.top_score)
    except Exception as e:  # record the failure, then surface it
        trace.update(total_ms=(time.perf_counter() - t0) * 1000, status="error", error=str(e)[:500])
        telemetry.record(trace)
        raise HTTPException(status_code=500, detail=f"internal error (trace {trace_id})") from e

    total_ms = (time.perf_counter() - t0) * 1000
    trace.update(**res.timings, llm_ms=ans.llm_ms, total_ms=total_ms, top_score=res.top_score,
                 n_chunks=len(res.hits), tokens_in=ans.tokens_in, tokens_out=ans.tokens_out,
                 cost_usd=ans.cost_usd, abstained=ans.abstained,
                 status="error" if ans.status == "llm_error" else ans.status, error=ans.error)
    telemetry.record(trace)
    return {"trace_id": trace_id, "answer": ans.text, "abstained": ans.abstained, "status": ans.status,
            "citations": ans.citations, "top_score": res.top_score, "mode": req.mode,
            "timings": {**res.timings, "llm_ms": ans.llm_ms, "total_ms": total_ms},
            "tokens_in": ans.tokens_in, "tokens_out": ans.tokens_out, "cost_usd": ans.cost_usd}
