"""Phase 1 check: plain cosine search over the HNSW index.

Usage: python -m scripts.sanity_query "landfill gas"
"""
from __future__ import annotations

import sys

import psycopg
from sentence_transformers import SentenceTransformer

from app.config import settings


def main(query: str, k: int = 5) -> None:
    """Print the k nearest chunks with doc, page and cosine similarity."""
    vec = SentenceTransformer(settings.embed_model, device="cpu").encode(query, normalize_embeddings=True)
    lit = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
    with psycopg.connect(settings.pg_dsn) as conn:
        print("rows:", conn.execute("SELECT count(*) FROM documents").fetchone()[0])
        rows = conn.execute(
            "SELECT doc_name, page, 1 - (embedding <=> %s::vector) AS sim, left(content, 160) "
            "FROM documents ORDER BY embedding <=> %s::vector LIMIT %s",
            (lit, lit, k),
        ).fetchall()
    for doc, page, sim, text in rows:
        print(f"{sim:.3f}  {doc} p.{page}  {text}")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "landfill gas")
