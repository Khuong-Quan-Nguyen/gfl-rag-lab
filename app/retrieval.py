"""Four retrieval modes behind one function: search(question, mode, k=10).

vector         cosine kNN over HNSW (vector_cosine_ops)
hybrid         vector top-50 + full-text top-50 fused with Reciprocal Rank Fusion (k=60)
vector_rerank  vector top-30 -> cross-encoder -> top-k
hybrid_rerank  hybrid top-30 -> cross-encoder -> top-k

Every hit carries `vector_sim` (cosine similarity to the question) so the abstain guardrail
uses the same scale whatever the mode; `score` is the mode's own ranking score.
"""
from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field

import psycopg

from app.config import settings

MODES = ("vector", "hybrid", "vector_rerank", "hybrid_rerank")
RRF_K = 60
FUSION_DEPTH = 50
RERANK_DEPTH = 30
RERANK_MAX_TOKENS = 256


@dataclass
class Hit:
    id: int
    doc_name: str
    page: int
    content: str
    score: float
    vector_sim: float


@dataclass
class SearchResult:
    mode: str
    hits: list[Hit]
    timings: dict[str, float] = field(default_factory=dict)  # embed_ms, retrieve_ms, rerank_ms

    @property
    def top_score(self) -> float:
        """Best cosine similarity among returned chunks (the 'thin context' warning signal)."""
        return max((h.vector_sim for h in self.hits), default=0.0)

    def to_dict(self) -> dict:
        return {"mode": self.mode, "top_score": self.top_score, "timings": self.timings,
                "hits": [asdict(h) for h in self.hits]}


class Models:
    """Embedder + cross-encoder, loaded once and shared (the long-lived-service fix)."""

    def __init__(self) -> None:
        self.embedder = None
        self.reranker = None
        self._lock = threading.Lock()

    def load(self, rerank: bool = True) -> "Models":
        from sentence_transformers import CrossEncoder, SentenceTransformer

        with self._lock:
            if self.embedder is None:
                self.embedder = SentenceTransformer(settings.embed_model, device="cpu")
            if rerank and self.reranker is None:
                # 256 tokens covers a ~180-word chunk + question; halves CPU rerank time vs the 512 default.
                self.reranker = CrossEncoder(settings.rerank_model, device="cpu", max_length=RERANK_MAX_TOKENS)
        return self


MODELS = Models()
_conn_lock = threading.Lock()
_conn: psycopg.Connection | None = None


def _db() -> psycopg.Connection:
    """One persistent autocommit connection (reconnects if dropped)."""
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(settings.pg_dsn, autocommit=True)
        _conn.execute("SET hnsw.ef_search = 100")
    return _conn


def _vec_literal(vec) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def _or_tsquery(conn: psycopg.Connection, question: str) -> str | None:
    """Stemmed question terms OR-ed together (AND would almost never match a full question)."""
    lexemes = conn.execute("SELECT tsvector_to_array(to_tsvector('english', %s))", (question,)).fetchone()[0]
    if not lexemes:
        return None
    return " | ".join("'" + l.replace("'", "''") + "'" for l in lexemes)


_COLS = "id, doc_name, page, content"


def _vector_candidates(conn, qvec: str, n: int) -> list[Hit]:
    rows = conn.execute(
        f"SELECT {_COLS}, 1 - (embedding <=> %s::vector) FROM documents ORDER BY embedding <=> %s::vector LIMIT %s",
        (qvec, qvec, n),
    ).fetchall()
    return [Hit(r[0], r[1], r[2], r[3], float(r[4]), float(r[4])) for r in rows]


def _keyword_candidates(conn, question: str, qvec: str, n: int) -> list[Hit]:
    tsq = _or_tsquery(conn, question)
    if tsq is None:
        return []
    rows = conn.execute(
        f"SELECT {_COLS}, ts_rank_cd(tsv, q), 1 - (embedding <=> %s::vector) "
        "FROM documents, to_tsquery('simple', %s) q WHERE tsv @@ q ORDER BY 5 DESC LIMIT %s",
        (qvec, tsq, n),
    ).fetchall()
    return [Hit(r[0], r[1], r[2], r[3], float(r[4]), float(r[5])) for r in rows]


def rrf_fuse(*ranked_lists: list[Hit], k: int = RRF_K) -> list[Hit]:
    """Reciprocal Rank Fusion: score = sum over lists of 1 / (k + rank)."""
    fused: dict[int, Hit] = {}
    scores: dict[int, float] = {}
    for hits in ranked_lists:
        for rank, h in enumerate(hits, start=1):
            fused.setdefault(h.id, h)
            scores[h.id] = scores.get(h.id, 0.0) + 1.0 / (k + rank)
    out = []
    for hid, s in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
        h = fused[hid]
        out.append(Hit(h.id, h.doc_name, h.page, h.content, s, h.vector_sim))
    return out


def search(question: str, mode: str = "hybrid", k: int = 10, models: Models | None = None) -> SearchResult:
    """Retrieve top-k chunks for `question` using one of MODES, with per-step timings in ms."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    models = models or MODELS
    rerank = mode.endswith("_rerank")
    models.load(rerank=rerank)
    timings = {"embed_ms": 0.0, "retrieve_ms": 0.0, "rerank_ms": 0.0}

    t0 = time.perf_counter()
    qvec = _vec_literal(models.embedder.encode(question, normalize_embeddings=True))
    timings["embed_ms"] = (time.perf_counter() - t0) * 1000

    depth = RERANK_DEPTH if rerank else k
    t0 = time.perf_counter()
    with _conn_lock:
        conn = _db()
        if mode.startswith("vector"):
            hits = _vector_candidates(conn, qvec, depth)
        else:
            hits = rrf_fuse(_vector_candidates(conn, qvec, FUSION_DEPTH),
                            _keyword_candidates(conn, question, qvec, FUSION_DEPTH))[:depth]
    timings["retrieve_ms"] = (time.perf_counter() - t0) * 1000

    if rerank and hits:
        t0 = time.perf_counter()
        scores = models.reranker.predict([(question, h.content) for h in hits])
        for h, s in zip(hits, scores):
            h.score = float(s)
        hits.sort(key=lambda h: h.score, reverse=True)
        timings["rerank_ms"] = (time.perf_counter() - t0) * 1000

    return SearchResult(mode, hits[:k], timings)
