from app.chunking import TARGET_WORDS, chunk_paragraphs, clean_text, split_sentences


def test_clean_joins_hyphenated_line_breaks_and_collapses_whitespace():
    assert clean_text("exam-\nple   text\n\nhere") == "example text here"


def test_split_sentences_respects_abbreviations():
    s = split_sentences("GFL Environmental Inc. operates in Canada. It also operates in the U.S. market. Done!")
    assert s == ["GFL Environmental Inc. operates in Canada.", "It also operates in the U.S. market.", "Done!"]


def _para(n_sentences: int, words_per_sentence: int = 12, tag: str = "P") -> str:
    return " ".join(
        f"{tag}{i} " + " ".join(["word"] * (words_per_sentence - 2)) + " end." for i in range(n_sentences)
    )


def test_chunks_stay_near_target_and_never_cut_sentences():
    paras = [_para(10, tag=f"A{j}_") for j in range(6)]  # 6 paragraphs x 120 words
    chunks = chunk_paragraphs(paras)
    assert len(chunks) > 1
    for c in chunks:
        assert c.endswith("end.")  # every chunk ends on a sentence boundary
        assert len(c.split()) <= TARGET_WORDS + 12  # at most one sentence over


def test_consecutive_chunks_overlap_by_a_sentence():
    chunks = chunk_paragraphs([_para(40)])
    assert len(chunks) >= 2
    tail = split_sentences(chunks[0])[-2:]  # overlap is 1-2 sentences
    assert chunks[1].startswith(tail[-1]) or chunks[1].startswith(" ".join(tail))


def test_short_paragraphs_are_packed_together():
    chunks = chunk_paragraphs(["One short paragraph here today.", "Another short one follows it now."])
    assert chunks == ["One short paragraph here today. Another short one follows it now."]
