import pytest

from eval.run_eval import compute_metrics, is_relevant


def test_is_relevant_by_name_and_by_path():
    chunk = {"name": "Flask.dispatch_request", "path": "src/flask/app.py"}
    assert is_relevant(chunk, {"names": ["dispatch_request"]})
    assert is_relevant(chunk, {"paths": ["flask/app.py"]})
    assert not is_relevant(chunk, {"names": ["dispatch"]})


def test_compute_metrics():
    rows = [{"hit1": True, "hit": True, "rr": 1.0, "prec": 0.2, "ms": 10},
            {"hit1": False, "hit": True, "rr": 0.5, "prec": 0.2, "ms": 30},
            {"hit1": False, "hit": False, "rr": 0.0, "prec": 0.0, "ms": 20}]
    m = compute_metrics(rows)
    assert m["recall_1"] == pytest.approx(1 / 3)
    assert m["recall_k"] == pytest.approx(2 / 3)
    assert m["mrr"] == pytest.approx(0.5)
    assert m["p50_ms"] == 20


def test_breakdown_by_type_and_disagreements():
    from eval.run_eval import breakdown
    d = {"vector": [{"q": "a", "type": "natural", "hit": True}, {"q": "b", "type": "docs", "hit": False}],
         "bm25": [{"q": "a", "type": "natural", "hit": False}, {"q": "b", "type": "docs", "hit": False}]}
    text = "\n".join(breakdown(d, 5))
    assert "| natural | 1 | 100% | 0% |" in text
    assert "| a | yes | NO |" in text and "| b | NO | NO |" in text
