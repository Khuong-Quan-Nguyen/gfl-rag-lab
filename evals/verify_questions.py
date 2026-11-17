"""Check every eval question against the PDFs before trusting it.

For each question: listed pages exist and are non-empty; for exact-term questions, the first
figure/name in the answer appears verbatim on at least one listed page.
A wrong test set is worse than none, so this runs before every eval change.

Usage: python -m evals.verify_questions
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import settings
from app.ingest import extract_pages

QUESTIONS = Path(__file__).with_name("questions.jsonl")
_FIGURE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?|[A-Z][a-z]+(?: [A-Z][a-z]+)+")


def load_questions() -> list[dict]:
    """Read questions.jsonl."""
    return [json.loads(l) for l in QUESTIONS.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    pages = {p.stem: [" ".join(paras) for paras in extract_pages(p)] for p in settings.raw_dir.glob("*.pdf")}
    qs = load_questions()
    problems = 0
    counts: dict[str, int] = {}
    for q in qs:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
        doc = pages.get(q["doc"])
        if doc is None:
            print(f"{q['id']}: unknown doc {q['doc']}"); problems += 1; continue
        texts = [doc[p - 1] if 1 <= p <= len(doc) else "" for p in q["pages"]]
        if not all(t.strip() for t in texts):
            print(f"{q['id']}: empty or missing page in {q['pages']}"); problems += 1; continue
        if q["type"] == "exact":
            m = _FIGURE.search(q["answer"])
            key = m.group(0).rstrip("%").lstrip("$") if m else None
            if not key or not any(key in t for t in texts):
                print(f"{q['id']}: key '{key}' not found on pages {q['pages']}"); problems += 1
    print(f"{len(qs)} questions {counts}; {problems} problem(s)")
    return problems


if __name__ == "__main__":
    raise SystemExit(main())
