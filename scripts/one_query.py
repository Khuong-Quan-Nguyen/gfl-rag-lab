"""One query in a fresh process: imports torch, loads both models, searches, exits.

This is the 'reload the model on every query' pattern the latency demo measures.
"""
from __future__ import annotations

import sys

from app.retrieval import Models, search

if __name__ == "__main__":
    question, mode = sys.argv[1], sys.argv[2]
    res = search(question, mode, k=10, models=Models().load(rerank=mode.endswith("_rerank")))
    print(res.hits[0].doc_name, res.hits[0].page)
