"""Send the eval questions (and the out-of-scope set) through POST /ask so the dashboard has traces.

Usage: python -m scripts.seed_traffic [--modes hybrid hybrid_rerank] [--limit 40]
Costs Claude tokens when ANTHROPIC_API_KEY is set (~1 request per question per mode).
"""
from __future__ import annotations

import argparse
import json
import urllib.request

from app.config import settings
from evals.verify_questions import load_questions
from scripts.calibrate_threshold import OUT_OF_SCOPE


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modes", nargs="+", default=["vector", "hybrid", "vector_rerank", "hybrid_rerank"])
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()
    questions = [q["question"] for q in load_questions()][: args.limit] + OUT_OF_SCOPE
    statuses: dict[str, int] = {}
    for mode in args.modes:
        for q in questions:
            req = urllib.request.Request(f"{settings.api_url}/ask", data=json.dumps({"question": q, "mode": mode}).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                s = json.loads(r.read())["status"]
            statuses[s] = statuses.get(s, 0) + 1
        print(f"{mode}: done")
    print("statuses:", statuses)


if __name__ == "__main__":
    main()
