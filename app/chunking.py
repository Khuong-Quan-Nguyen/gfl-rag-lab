"""Text cleaning and paragraph-aware chunking (after Arvind Pant's RAG article).

Rules: ~180 words per chunk (under MiniLM's 256-token limit), paragraphs kept whole
when they fit, long paragraphs split on sentence boundaries, 1-2 sentences of overlap
between consecutive chunks, and never a cut in the middle of a sentence.
"""
from __future__ import annotations

import re

TARGET_WORDS = 180
OVERLAP_MAX_WORDS = 40
MIN_CHUNK_WORDS = 8

_HYPHEN_BREAK = re.compile(r"(\w)-\s*\n\s*(\w)")
_WS = re.compile(r"\s+")
_ABBREV = re.compile(r"\b(?:Inc|Corp|Ltd|Co|No|Nos|Mr|Mrs|Ms|Dr|St|vs|approx|e\.g|i\.e|U\.S|etc)\.$", re.I)
_SENT_END = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(\[$])")


def clean_text(text: str) -> str:
    """Join words hyphenated across line breaks, normalize quotes, collapse whitespace."""
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    text = text.replace("­", "").replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"').replace("�", "'")
    return _WS.sub(" ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split on sentence-ending punctuation, but not after common abbreviations."""
    parts, start = [], 0
    for m in _SENT_END.finditer(text):
        candidate = text[start:m.start()].strip()
        if _ABBREV.search(candidate):
            continue
        if candidate:
            parts.append(candidate)
        start = m.end()
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _words(s: str) -> int:
    return len(s.split())


def _overlap(sentences: list[str]) -> list[str]:
    """Last 1-2 sentences of a chunk, capped at OVERLAP_MAX_WORDS."""
    out: list[str] = []
    for s in reversed(sentences[-2:]):
        if _words(s) + sum(_words(x) for x in out) > OVERLAP_MAX_WORDS:
            break
        out.insert(0, s)
    return out


def _cap_long(sentences: list[str], target: int) -> list[str]:
    """Break 'sentences' longer than the target (tables, lists without punctuation) into word windows.

    The only place a cut can land mid-'sentence'; real prose sentences are never this long.
    """
    out: list[str] = []
    for s in sentences:
        w = s.split()
        if len(w) <= target:
            out.append(s)
        else:
            out.extend(" ".join(w[i:i + target]) for i in range(0, len(w), target))
    return out


def chunk_paragraphs(paragraphs: list[str], target: int = TARGET_WORDS) -> list[str]:
    """Pack cleaned paragraphs into ~target-word chunks with sentence overlap.

    Units are sentences; a paragraph's sentences stay together unless the paragraph
    alone exceeds the target. A sentence longer than the target becomes its own chunk.
    """
    chunks: list[str] = []
    current: list[str] = []
    fresh = 0  # sentences in `current` that are not overlap carried from the previous chunk

    def flush() -> None:
        nonlocal current, fresh
        if fresh and _words(" ".join(current)) >= MIN_CHUNK_WORDS:
            chunks.append(" ".join(current))
            current = _overlap(current)
        elif fresh:  # too small to stand alone: keep for the next chunk
            return
        fresh = 0

    for para in paragraphs:
        sents = _cap_long(split_sentences(para), target)
        if not sents:
            continue
        para_words = sum(_words(s) for s in sents)
        # Paragraph fits in the current chunk whole -> add it whole.
        if _words(" ".join(current)) + para_words <= target:
            current.extend(sents)
            fresh += len(sents)
            continue
        # Otherwise close the current chunk at the paragraph boundary, then add sentence by sentence.
        flush()
        for s in sents:
            if fresh and _words(" ".join(current)) + _words(s) > target:
                flush()
            current.append(s)
            fresh += 1
    if fresh:
        text = " ".join(current)
        if _words(text) >= MIN_CHUNK_WORDS or not chunks:
            chunks.append(text)
    return [c for c in chunks if c.strip()]
