"""Answer step: Claude answers only from retrieved chunks, cites [doc p.N], and abstains on thin context.

Guardrail: if the best cosine similarity among retrieved chunks is below ABSTAIN_THRESHOLD,
the LLM is skipped entirely and the service returns NOT_FOUND.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import anthropic

from app.config import settings
from app.retrieval import Hit

NOT_FOUND = "Not found in the GFL documents."
CONTEXT_CHUNKS = 5
# USD per million tokens (input, output) for cost tracking on the dashboard.
PRICING = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}

SYSTEM = f"""You answer questions about GFL Environmental using only the numbered context passages provided.
Rules:
- Use only facts stated in the passages. Do not use outside knowledge.
- After each sentence that uses a passage, cite it exactly as its label, e.g. [sustainability_2024 p.13].
- Quote figures exactly as written, with units and the year they refer to.
- If the passages do not contain the answer, reply exactly: {NOT_FOUND}
- Keep the answer to at most 4 sentences."""


@dataclass
class Answer:
    text: str
    abstained: bool
    citations: list[dict] = field(default_factory=list)
    llm_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    status: str = "ok"  # ok | abstained | no_api_key | llm_error | refusal
    error: str | None = None


def _label(h: Hit) -> str:
    return f"{h.doc_name} p.{h.page}"


def build_context(hits: list[Hit]) -> str:
    """Format the top chunks as labelled passages."""
    return "\n\n".join(f"<passage label=\"[{_label(h)}]\">\n{h.content}\n</passage>" for h in hits[:CONTEXT_CHUNKS])


def citations_for(hits: list[Hit]) -> list[dict]:
    return [{"doc": h.doc_name, "page": h.page, "score": h.score, "similarity": h.vector_sim,
             "snippet": h.content[:240]} for h in hits[:CONTEXT_CHUNKS]]


def cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRICING.get(model, (0.0, 0.0))
    return (tokens_in * pin + tokens_out * pout) / 1_000_000


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None, max_retries=2, timeout=60.0)
    return _client


def answer(question: str, hits: list[Hit], top_score: float) -> Answer:
    """Abstain on low similarity; otherwise ask Claude for a cited answer from the top chunks."""
    cites = citations_for(hits)
    if not hits or top_score < settings.abstain_threshold:
        return Answer(NOT_FOUND, True, [], status="abstained")
    if not settings.anthropic_api_key:
        return Answer("Answer step disabled: set ANTHROPIC_API_KEY in .env. The retrieved passages are listed below.",
                      False, cites, status="no_api_key")

    t0 = time.perf_counter()
    try:
        resp = _get_client().beta.messages.create(
            model=settings.claude_model,
            max_tokens=16000,
            system=SYSTEM,
            output_config={"effort": "low"},  # short grounded Q&A: low effort keeps latency down
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # re-run on a fallback model if the request is declined
            messages=[{"role": "user", "content": f"{build_context(hits)}\n\nQuestion: {question}"}],
        )
    except anthropic.RateLimitError as e:
        return Answer(NOT_FOUND, False, cites, status="llm_error", error=f"rate limited: {e.message}")
    except anthropic.APIStatusError as e:
        return Answer(NOT_FOUND, False, cites, status="llm_error", error=f"{e.status_code}: {e.message}")
    except anthropic.APIConnectionError as e:
        return Answer(NOT_FOUND, False, cites, status="llm_error", error=f"connection: {e}")
    llm_ms = (time.perf_counter() - t0) * 1000

    usage = resp.usage
    tin, tout = usage.input_tokens, usage.output_tokens
    out = Answer("", False, cites, llm_ms, tin, tout, cost(settings.claude_model, tin, tout))
    if resp.stop_reason == "refusal":
        out.text, out.status = NOT_FOUND, "refusal"
        return out
    out.text = "".join(b.text for b in resp.content if b.type == "text").strip() or NOT_FOUND
    out.abstained = out.text.startswith(NOT_FOUND)
    return out
