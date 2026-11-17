"""Phase 2 check: run one question through all four modes and print top hits + timings.

Usage: python -m scripts.try_modes "How much RNG does GFL produce?"
"""
from __future__ import annotations

import sys

from app.retrieval import MODES, search


def main(question: str) -> None:
    for mode in MODES:
        r = search(question, mode, k=3)
        t = ", ".join(f"{k}={v:.0f}" for k, v in r.timings.items())
        print(f"\n[{mode}] top_score={r.top_score:.3f}  ({t})")
        for h in r.hits:
            print(f"  {h.score:8.4f}  {h.doc_name} p.{h.page}  {h.content[:110]}")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "What did GFL do at the Central Missouri landfill?")
