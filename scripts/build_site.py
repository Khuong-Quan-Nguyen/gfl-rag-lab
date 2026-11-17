"""Build the static showcase data file (site/data.js) from the latest eval run, the latency demo and the questions.

The raw results in evals/results/ are gitignored, so the generated site/data.js is committed and
Vercel serves site/ as plain static files (no build step, no Python).

Usage: python -m scripts.build_site
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings
from evals.verify_questions import load_questions

SITE = Path(__file__).resolve().parent.parent / "site"


def latest_eval(results_dir: Path) -> dict:
    """Return the most recent timestamped eval run (files are named by ISO timestamp)."""
    runs = sorted(p for p in results_dir.glob("2*.json"))
    if not runs:
        raise SystemExit("No eval results found: run `python -m evals.run_evals` first.")
    return json.loads(runs[-1].read_text(encoding="utf-8"))


def ranks_by_question(per_question: list[dict]) -> dict[str, dict[str, int | None]]:
    """Map question id -> {mode: rank or None if missed within k}."""
    out: dict[str, dict[str, int | None]] = {}
    for row in per_question:
        out.setdefault(row["id"], {})[row["mode"]] = row["rank"]
    return out


def build_payload() -> dict:
    """Collect everything the static page renders into one JSON-serialisable dict."""
    run = latest_eval(settings.results_dir)
    latency = json.loads((settings.results_dir / "latency_demo.json").read_text(encoding="utf-8"))
    ranks = ranks_by_question(run["per_question"])
    questions = [{"id": q["id"], "type": q["type"], "doc": q["doc"], "pages": q["pages"],
                  "question": q["question"], "answer": q["answer"], "ranks": ranks.get(q["id"], {})}
                 for q in load_questions()]
    return {
        "timestamp": run["timestamp"], "k": run["k"], "page_tolerance": run["page_tolerance"],
        "embed_model": run["embed_model"], "rerank_model": run["rerank_model"],
        "table": run["table"],
        "latency": {"mode": latency["mode"], "cold_ms": latency["cold_ms"], "warm_ms": latency["warm_ms"],
                    "p50_cold_ms": latency["p50_cold_ms"], "p50_warm_ms": latency["p50_warm_ms"]},
        "questions": questions,
    }


def main() -> None:
    SITE.mkdir(exist_ok=True)
    payload = build_payload()
    out = SITE / "data.js"
    out.write_text("window.LAB = " + json.dumps(payload, indent=1) + ";\n", encoding="utf-8")
    print(f"wrote {out} ({len(payload['questions'])} questions, run {payload['timestamp']})")


if __name__ == "__main__":
    main()
