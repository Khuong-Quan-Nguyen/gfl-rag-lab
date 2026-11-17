"""Retrieval eval: recall@10, top-1 and MRR for 4 modes x 2 question types, +-1 page tolerance.

A hit counts as relevant when it comes from the question's doc and its page is within
+-1 of any labelled answer page. Every run is saved to evals/results/<timestamp>.json.

Usage: python -m evals.run_evals [--k 10]
"""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime

from app.config import settings
from app.retrieval import MODELS, MODES, Hit, search
from evals.verify_questions import load_questions

PAGE_TOLERANCE = 1


def first_relevant_rank(hits: list[Hit], doc: str, pages: list[int]) -> int | None:
    """1-based rank of the first relevant hit, or None."""
    for rank, h in enumerate(hits, start=1):
        if h.doc_name == doc and any(abs(h.page - p) <= PAGE_TOLERANCE for p in pages):
            return rank
    return None


def summarize(ranks: list[int | None], k: int) -> dict[str, float]:
    """recall@k, top-1 and MRR over a list of first-relevant ranks."""
    n = len(ranks) or 1
    return {
        f"recall@{k}": sum(r is not None and r <= k for r in ranks) / n,
        "top1": sum(r == 1 for r in ranks) / n,
        "mrr": sum(1 / r for r in ranks if r) / n,
        "n": len(ranks),
    }


def run(k: int = 10) -> dict:
    """Run every question through every mode and return the full result record."""
    MODELS.load(rerank=True)
    questions = load_questions()
    search(questions[0]["question"], "hybrid_rerank", k=k)  # warm-up, not timed
    per_question, table = [], {}
    for mode in MODES:
        latencies = []
        by_type: dict[str, list[int | None]] = {"conceptual": [], "exact": []}
        for q in questions:
            res = search(q["question"], mode, k=k)
            rank = first_relevant_rank(res.hits, q["doc"], q["pages"])
            by_type[q["type"]].append(rank)
            latencies.append(sum(res.timings.values()))
            per_question.append({"id": q["id"], "type": q["type"], "mode": mode, "rank": rank,
                                 "top_score": res.top_score,
                                 "top_hit": f"{res.hits[0].doc_name} p.{res.hits[0].page}" if res.hits else None})
        table[mode] = {t: summarize(r, k) for t, r in by_type.items()}
        table[mode]["all"] = summarize(by_type["conceptual"] + by_type["exact"], k)
        table[mode]["p50_ms"] = statistics.median(latencies)
    return {"timestamp": datetime.now().isoformat(timespec="seconds"), "k": k,
            "page_tolerance": PAGE_TOLERANCE, "n_questions": len(questions),
            "embed_model": settings.embed_model, "rerank_model": settings.rerank_model,
            "table": table, "per_question": per_question}


def print_table(result: dict) -> None:
    """Render mode x type metrics as a plain-text table."""
    k = result["k"]
    print(f"\n{result['n_questions']} questions, k={k}, +-{result['page_tolerance']} page tolerance\n")
    print(f"{'mode':<15}{'type':<12}{f'recall@{k}':>10}{'top1':>8}{'MRR':>8}{'p50 ms':>9}")
    for mode, row in result["table"].items():
        for t in ("conceptual", "exact", "all"):
            m = row[t]
            p50 = f"{row['p50_ms']:.0f}" if t == "all" else ""
            print(f"{mode:<15}{t:<12}{m[f'recall@{k}']:>10.3f}{m['top1']:>8.3f}{m['mrr']:>8.3f}{p50:>9}")
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k", type=int, default=10)
    args = ap.parse_args()
    result = run(args.k)
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    out = settings.results_dir / f"{result['timestamp'].replace(':', '-')}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print_table(result)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
