"""Central settings, read once from .env / environment."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime configuration. Secrets come only from .env / environment."""

    pg_dsn: str = os.getenv("PG_DSN", "postgresql://rag:rag@localhost:5433/gfl")
    embed_model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    rerank_model: str = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    abstain_threshold: float = float(os.getenv("ABSTAIN_THRESHOLD", "0.38"))
    api_url: str = os.getenv("API_URL", "http://127.0.0.1:8000")
    raw_dir: Path = ROOT / "data" / "raw"
    results_dir: Path = ROOT / "evals" / "results"


settings = Settings()
