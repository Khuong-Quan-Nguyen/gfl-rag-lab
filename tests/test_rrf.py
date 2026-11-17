from app.retrieval import Hit, rrf_fuse


def _h(i: int) -> Hit:
    return Hit(id=i, doc_name="d", page=i, content=str(i), score=0.0, vector_sim=0.1 * i)


def test_rrf_rewards_items_ranked_in_both_lists():
    a = [_h(1), _h(2), _h(3)]
    b = [_h(3), _h(4)]
    fused = rrf_fuse(a, b, k=60)
    assert fused[0].id == 3  # 1/63 + 1/61 beats 1/61 alone
    assert {h.id for h in fused} == {1, 2, 3, 4}


def test_rrf_keeps_vector_similarity():
    fused = rrf_fuse([_h(2)], [])
    assert fused[0].vector_sim == 0.2
