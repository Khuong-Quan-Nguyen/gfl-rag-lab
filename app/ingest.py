"""PDF -> clean -> chunk -> embed -> COPY into Postgres.

Usage:
    python -m app.ingest              # ingest every PDF in data/raw (replaces those docs' rows)
    python -m app.ingest --dry-run    # extract + chunk only, print stats
"""
from __future__ import annotations

import argparse
import collections
import re
import time
from dataclasses import dataclass
from pathlib import Path

import pymupdf
import psycopg

from app.chunking import chunk_paragraphs, clean_text
from app.config import settings

BLOCK_REPEAT_FRAC = 0.15  # a block repeated on >=15% of pages is a header/footer/nav bar
LINE_REPEAT_FRAC = 0.40   # a single line repeated on >=40% of pages likewise
MIN_PAGES_FOR_REPEAT = 5


@dataclass
class Chunk:
    doc_name: str
    doc_year: int | None
    page: int  # 1-based, as printed by a PDF viewer
    chunk_idx: int
    content: str


def _norm(s: str) -> str:
    """Normalize for repeat detection: digits -> #, whitespace collapsed, lowercased."""
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", s)).strip().lower()


def _doc_meta(path: Path) -> tuple[str, int | None]:
    name = path.stem.lower()
    year = re.search(r"(20\d\d)", name)
    return name, int(year.group(1)) if year else None


def extract_pages(path: Path) -> list[list[str]]:
    """Return, per page, the list of cleaned paragraph blocks with headers/footers removed."""
    doc = pymupdf.open(path)
    raw: list[list[str]] = []
    for page in doc:
        blocks = [b[4] for b in page.get_text("blocks", sort=True) if b[6] == 0]  # text blocks only
        raw.append(blocks)

    n = len(raw)
    block_freq: collections.Counter[str] = collections.Counter()
    line_freq: collections.Counter[str] = collections.Counter()
    for blocks in raw:
        block_freq.update({_norm(b) for b in blocks})
        line_freq.update({_norm(l) for b in blocks for l in b.splitlines() if l.strip()})

    def repeated(counter: collections.Counter[str], key: str, frac: float) -> bool:
        return n >= MIN_PAGES_FOR_REPEAT and counter[key] >= max(2, frac * n)

    pages: list[list[str]] = []
    for blocks in raw:
        paras = []
        for b in blocks:
            if repeated(block_freq, _norm(b), BLOCK_REPEAT_FRAC):
                continue
            lines = [l for l in b.splitlines() if not repeated(line_freq, _norm(l), LINE_REPEAT_FRAC)]
            text = clean_text("\n".join(lines))
            if re.fullmatch(r"[\W\d_]*", text):  # page numbers, bullets, empty
                continue
            paras.append(text)
        pages.append(paras)
    return pages


def chunk_pdf(path: Path) -> list[Chunk]:
    """Chunk one PDF page by page so every chunk maps to exactly one page."""
    doc_name, doc_year = _doc_meta(path)
    out: list[Chunk] = []
    for pno, paras in enumerate(extract_pages(path), start=1):
        for i, text in enumerate(chunk_paragraphs(paras)):
            out.append(Chunk(doc_name, doc_year, pno, i, text))
    return out


def load(chunks: list[Chunk], batch_size: int = 64) -> int:
    """Embed in batches and bulk-load with COPY. Replaces rows of the same doc_name."""
    from sentence_transformers import SentenceTransformer  # heavy import, only when loading

    model = SentenceTransformer(settings.embed_model, device="cpu")
    t0 = time.perf_counter()
    vecs = model.encode([c.content for c in chunks], batch_size=batch_size,
                        normalize_embeddings=True, show_progress_bar=True)
    print(f"embedded {len(chunks)} chunks in {time.perf_counter() - t0:.1f}s")

    with psycopg.connect(settings.pg_dsn) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE doc_name = ANY(%s)", (sorted({c.doc_name for c in chunks}),))
        with cur.copy("COPY documents (doc_name, doc_year, page, chunk_idx, content, embedding) FROM STDIN") as cp:
            for c, v in zip(chunks, vecs):
                cp.write_row((c.doc_name, c.doc_year, c.page, c.chunk_idx, c.content,
                              "[" + ",".join(f"{x:.6f}" for x in v) + "]"))
        cur.execute("ANALYZE documents")
        return cur.execute("SELECT count(*) FROM documents").fetchone()[0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pdfs = sorted(settings.raw_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs in {settings.raw_dir}")
    chunks: list[Chunk] = []
    for p in pdfs:
        cs = chunk_pdf(p)
        words = [len(c.content.split()) for c in cs]
        print(f"{p.name}: {len(cs)} chunks, avg {sum(words) / max(1, len(words)):.0f} words, max {max(words, default=0)}")
        chunks.extend(cs)
    if args.dry_run:
        return
    print("rows in documents:", load(chunks))


if __name__ == "__main__":
    main()
