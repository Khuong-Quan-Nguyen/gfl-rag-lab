"""Cold-load-per-query vs long-lived service: p50 latency over the same 10 queries.

Cold:  a fresh Python process per query (import torch + load embedder and cross-encoder + search),
       i.e. the original 7-second bug from 'Building RAG You Can Trust'.
Warm:  the same queries via POST /search on the FastAPI service, models loaded once at startup.
       Starts the service itself if it is not already running.

Usage: python -m scripts.latency_demo [--mode hybrid_rerank] [--n 10]
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
import urllib.request

from app.config import ROOT, settings
from evals.verify_questions import load_questions


def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(f"{settings.api_url}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _healthy() -> bool:
    try:
        with urllib.request.urlopen(f"{settings.api_url}/health", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def cold(questions: list[str], mode: str) -> list[float]:
    out = []
    for i, q in enumerate(questions, 1):
        t0 = time.perf_counter()
        subprocess.run([sys.executable, "-m", "scripts.one_query", q, mode], cwd=ROOT, check=True,
                       capture_output=True)
        out.append((time.perf_counter() - t0) * 1000)
        print(f"  cold {i:2d}: {out[-1]:7.0f} ms")
    return out


def warm(questions: list[str], mode: str) -> list[float]:
    out = []
    for i, q in enumerate(questions, 1):
        t0 = time.perf_counter()
        _post("/search", {"question": q, "mode": mode})
        out.append((time.perf_counter() - t0) * 1000)
        print(f"  warm {i:2d}: {out[-1]:7.0f} ms")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="hybrid_rerank")
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()
    questions = [q["question"] for q in load_questions()][: args.n]

    print(f"Cold: model reloaded per query ({args.mode})")
    cold_ms = cold(questions, args.mode)

    server = None
    if not _healthy():
        port = settings.api_url.rsplit(":", 1)[-1]
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.service:app", "--port", port],
                                  cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(120):
            if _healthy():
                break
            time.sleep(1)
    try:
        print(f"Warm: long-lived service, models loaded once ({args.mode})")
        warm_ms = warm(questions, args.mode)
    finally:
        if server:
            server.terminate()

    c50, w50 = statistics.median(cold_ms), statistics.median(warm_ms)
    print(f"\np50 cold (reload per query): {c50:,.0f} ms")
    print(f"p50 warm (long-lived service): {w50:,.0f} ms")
    print(f"speed-up: {c50 / w50:.1f}x")
    out = settings.results_dir / "latency_demo.json"
    out.write_text(json.dumps({"mode": args.mode, "cold_ms": cold_ms, "warm_ms": warm_ms,
                               "p50_cold_ms": c50, "p50_warm_ms": w50}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
