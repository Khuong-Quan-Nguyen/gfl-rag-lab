import dataclasses

import app.generate as gen
from app.retrieval import Hit

HITS = [Hit(1, "sustainability_2024", 13, "RNG facility text", 1.0, 0.6)]


def _settings(**kw):
    return dataclasses.replace(gen.settings, **kw)


def test_abstains_below_threshold_without_calling_llm(monkeypatch):
    monkeypatch.setattr(gen, "settings", _settings(abstain_threshold=0.7, anthropic_api_key="sk-test"))
    monkeypatch.setattr(gen, "_get_client", lambda: (_ for _ in ()).throw(AssertionError("LLM called")))
    a = gen.answer("q", HITS, top_score=0.6)
    assert a.abstained and a.text == gen.NOT_FOUND and a.status == "abstained"


def test_no_api_key_returns_passages_instead_of_failing(monkeypatch):
    monkeypatch.setattr(gen, "settings", _settings(abstain_threshold=0.3, anthropic_api_key=""))
    a = gen.answer("q", HITS, top_score=0.6)
    assert a.status == "no_api_key" and not a.abstained and a.citations[0]["page"] == 13


def test_context_labels_match_citation_format():
    assert '[sustainability_2024 p.13]' in gen.build_context(HITS)


def test_cost_uses_per_million_pricing():
    assert gen.cost("claude-opus-5-5", 1_000_000, 0) == 4.0
