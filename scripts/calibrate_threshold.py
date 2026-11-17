"""Pick ABSTAIN_THRESHOLD: out-of-scope questions should fall below it, all 40 eval questions above.

Usage: python -m scripts.calibrate_threshold [--mode hybrid_rerank]
"""
from __future__ import annotations

import argparse

from app.retrieval import search
from evals.verify_questions import load_questions

OUT_OF_SCOPE = [
    "What is GFL's stock price today?",
    "Who won the Stanley Cup?",
    "What is the capital of Australia?",
    "How do I bake sourdough bread at home?",
    "What is the best smartphone to buy this year?",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="hybrid_rerank")
    mode = ap.parse_args().mode

    in_scope = sorted((search(q["question"], mode).top_score, q["id"]) for q in load_questions())
    oos = sorted(((search(q, mode).top_score, q) for q in OUT_OF_SCOPE), reverse=True)
    print("lowest in-scope top_scores:")
    for s, qid in in_scope[:5]:
        print(f"  {s:.3f}  {qid}")
    print("out-of-scope top_scores:")
    for s, q in oos:
        print(f"  {s:.3f}  {q}")
    lo_in, hi_out = in_scope[0][0], oos[0][0]
    if hi_out < lo_in:
        print(f"\nclean gap: ({hi_out:.3f}, {lo_in:.3f}) -> suggested ABSTAIN_THRESHOLD={(hi_out + lo_in) / 2:.2f}")
    else:
        print(f"\nno clean gap: highest out-of-scope {hi_out:.3f} >= lowest in-scope {lo_in:.3f}")


if __name__ == "__main__":
    main()
